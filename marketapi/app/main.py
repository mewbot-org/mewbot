import pandas as pd
import asyncio
import asyncpg
import os
import uvicorn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from fastapi import FastAPI
import ujson as json

# Initialize the FastAPI app
app = FastAPI()

DATABASE = os.environ["DATABASE_URL"]

# Global variables to store the trained model and scaler
model = None
scaler = None


async def fetch_trade_data(pool, start_pokname, end_pokname):
    query = """
    WITH trade_data AS (
        SELECT
            p.pokname,
            COUNT(t.t_id) AS trade_frequency,
            AVG(t.sender_credits + t.receiver_credits) AS avg_trade_value,
            COUNT(p.id) AS scarcity
        FROM trade_logs t
        JOIN pokes p ON p.id = ANY(t.sender_pokes) OR p.id = ANY(t.receiver_pokes)
        WHERE t.sender_credits > 10000 OR t.receiver_credits > 10000
          AND p.pokname BETWEEN $1 AND $2
        GROUP BY p.pokname, p.id
    )
    SELECT
        td.pokname,
        trade_frequency,
        avg_trade_value,
        scarcity,
        (trade_frequency * avg_trade_value) / (scarcity + 1) AS demand_score
    FROM trade_data td;
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, start_pokname, end_pokname)
        data = pd.DataFrame(
            rows,
            columns=[
                "pokname",
                "trade_frequency",
                "avg_trade_value",
                "scarcity",
                "demand_score",
            ],
        )
    return data


async def fetch_iv_totals(pool, start_pokname, end_pokname):
    query = """
    SELECT
        p.pokname,
        COALESCE((COALESCE(atkiv, 0) + COALESCE(defiv, 0) + COALESCE(spatkiv, 0) + 
                  COALESCE(spdefiv, 0) + COALESCE(speediv, 0)), 0) AS iv_total
    FROM pokes p
    WHERE p.pokname BETWEEN $1 AND $2;
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, start_pokname, end_pokname)
        iv_totals = pd.DataFrame(rows, columns=["pokname", "iv_total"])
    return iv_totals


async def fetch_skins(pool, start_pokname, end_pokname):
    query = """
    SELECT
        p.pokname,
        p.skin
    FROM pokes p
    WHERE p.pokname BETWEEN $1 AND $2;
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, start_pokname, end_pokname)
        skin_multipliers = pd.DataFrame(rows, columns=["pokname", "skin_multiplier"])
    return skin_multipliers


async def merge_data(pool, start_pokname, end_pokname):
    # Fetch data in chunks
    trade_data = await fetch_trade_data(pool, start_pokname, end_pokname)
    iv_totals = await fetch_iv_totals(pool, start_pokname, end_pokname)
    skins = await fetch_skins(pool, start_pokname, end_pokname)

    # Merge all data based on pokname
    merged_data = trade_data.merge(iv_totals, on="pokname").merge(skins, on="pokname")
    return merged_data


@app.on_event("startup")
async def startup():
    async def init(con):
        await con.set_type_codec(
            typename="json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )
        await con.execute("SET statement_timeout = '60000';")

    app.pool = await asyncpg.create_pool(DATABASE, init=init)
    print("Pool has been Created Successfully!")

    print("Model and Scaler are Ready!")


# Asynchronous function to fetch data from the database
async def fetch_data():
    async with app.pool.acquire() as conn:
        sql_query = """WITH trade_data AS (
                        SELECT
                            p.pokname,
                            COUNT(t.t_id) AS trade_frequency,
                            AVG(t.sender_credits + t.receiver_credits) AS avg_trade_value
                        FROM trade_logs t
                        JOIN pokes p ON p.id = ANY(t.sender_pokes) OR p.id = ANY(t.receiver_pokes)
                        WHERE t.sender_credits > 10000 OR t.receiver_credits > 10000 
                        GROUP BY p.pokname, p.id
                    )
                    SELECT
                        td.pokname,  -- Disambiguate pokname by specifying td (alias for trade_data)
                        trade_frequency,
                        avg_trade_value,
                        p.skin,
                        COALESCE((COALESCE(atkiv, 0) + COALESCE(defiv, 0) + COALESCE(spatkiv, 0) + COALESCE(spdefiv, 0) + COALESCE(speediv, 0)), 0) AS iv_total
                    FROM trade_data td
                    JOIN pokes p ON p.pokname = td.pokname  -- Join condition should also reference td.pokname

        """

        rows = await conn.fetch(sql_query)
        # Use pandas to create DataFrame from rows, and get column names from the query result
        columns = [
            "pokname",
            "trade_frequency",
            "avg_trade_value",
            "scarcity",
            "skin",
            "iv_total",
        ]
        data = pd.DataFrame(rows, columns=columns)
        return data


# Function to preprocess the data and train the model
def process_and_train(data):
    # Features and target (price is assumed to be available in your data)

    X = data[["demand_score", "skin", "iv_total", "avg_trade_value"]]
    y = data["price"]  # Replace with actual price column if available

    # Split into train and test sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Normalize/scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Model - Random Forest Regressor (you can experiment with other models)
    model = RandomForestRegressor(n_estimators=100, random_state=42)

    # Train the model
    model.fit(X_train_scaled, y_train)

    # Predict on the test set
    y_pred = model.predict(X_test_scaled)

    # Evaluate the model
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Mean Absolute Error: {mae}")

    return model, scaler  # Return the trained model and scaler


# Function to predict the price of a Pokémon using the trained model
async def predict_price(pokname: str):
    # Fetch data asynchronously from the database
    start_pokname = pokname[
        0
    ].upper()  # Use the first character as a range start (example strategy)
    end_pokname = pokname[
        0
    ].upper()  # Use the same for the end for simplicity, adjust as needed

    # Fetch and merge data
    merged_data = await merge_data(app.pool, start_pokname, end_pokname)

    # Now you can proceed to use the merged data for model prediction
    pokemon_data = merged_data[merged_data["pokname"] == pokname].iloc[0]

    # Prepare the features
    features = [
        pokemon_data["demand_score"],
        pokemon_data["skin"],
        pokemon_data["iv_total"],
        # pokemon_data['rarity_multiplier'],
        pokemon_data["avg_trade_value"],
    ]

    global model, scaler
    model, scaler = process_and_train(pokemon_data)
    print("Done Training")
    # Normalize the features
    scaled_features = scaler.transform([features])

    # Predict the price
    predicted_price = model.predict(scaled_features)[0]

    return predicted_price


# FastAPI endpoint to get the price suggestion for a given pokname
@app.get("/predict_price/{pokname}")
async def get_price(pokname: str):
    predicted_price = await predict_price(pokname)
    return {"pokname": pokname, "predicted_price": predicted_price}


# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=15211)
