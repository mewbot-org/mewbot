import numpy as np
from starlette.responses import StreamingResponse
from fastapi import FastAPI, Query
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pymemcache.client import base
from pymemcache import serde
from typing import List, Dict
from sklearn.ensemble import RandomForestClassifier

import pandas as pd
import orjson
import math
import io

from helpers import HealthBar, sresize


app = FastAPI()
app.mc = base.Client(("178.28.0.20", 11211), serde=serde.PickleSerde(pickle_version=2))
DIR = Path(__file__).parent / "res"
PRELOADED = {
    "trick_room": Image.open(str(DIR / "trick_room.png")).convert("RGBA"),
    "rain": Image.open(str(DIR / "rain.png")).convert("RGBA"),
    "hail": Image.open(str(DIR / "hail.png")).convert("RGBA"),
    "sun": Image.open(str(DIR / "sun.png")).convert("RGBA"),
    "sandstorm": Image.open(str(DIR / "sandstorm.png")).convert("RGBA"),
    "sub": sresize(Image.open(str(DIR / "sub.png"))).convert("RGBA"),
    "preview_sub": sresize(
        Image.open(str(DIR / "sub.png")), dimensions=(64, 64)
    ).convert("RGBA"),
}

font = ImageFont.truetype(str(DIR / "futur.ttf"), 16, encoding="unic")


def draw_rectangle(width, height, color):
    """
    Draw a rectangle.
    """
    rectangle = Image.new("RGBA", (width, height), color)
    return rectangle


def draw_pixel_pokemon_card(path, level, gender="-m"):
    """Parameters
    path: str
        Path to image
    """
    base_card_width, base_card_height = 272, 75

    base_card = draw_rectangle(base_card_width, base_card_height, "#f5f5f5").convert(
        "RGBA"
    )
    try:
        with Image.open(DIR / path).convert("RGBA") as pokemon_sprite:
            base_card.paste(pokemon_sprite, (5, -10), mask=pokemon_sprite)
    except:
        base_card.paste(
            PRELOADED["preview_sub"], (5, -10), mask=PRELOADED["preview_sub"]
        )

    draw = ImageDraw.Draw(base_card)
    draw.text(
        (140, 40), f"Lv.{level}", anchor="mm", fill="black", align="center", font=font
    )
    return base_card


def draw_player_headers(background, names):
    top = 200
    rect_w, rect_h = 282, 37
    rects = draw_rectangle(rect_w, rect_h, "#0000FF"), draw_rectangle(
        rect_w, rect_h, "#FF0000"
    )
    draw = ImageDraw.Draw(rects[0])
    draw.text(
        ((rect_w / 2), (rect_h / 2)),
        names[0],
        anchor="mm",
        fill="white",
        align="center",
        font=font,
    )
    background.paste(rects[0], (top, 38))
    draw = ImageDraw.Draw(rects[1])
    draw.text(
        ((rect_w / 2), (rect_h / 2)),
        names[1],
        anchor="mm",
        fill="white",
        align="center",
        font=font,
    )
    background.paste(rects[1], (top + 600, 38))


def draw_player_teams(background, p1pokes, p2pokes):
    # Draw First Player Team
    left = 125
    for pokemon, level in p1pokes:
        base_card = draw_pixel_pokemon_card(pokemon, level)
        background.paste(base_card, (205, left - 45), mask=base_card)
        left += 80

    # Draw Second Player Team
    left = 125
    for pokemon, level in p2pokes:
        base_card = draw_pixel_pokemon_card(pokemon, level)
        background.paste(base_card, (804, left - 45), mask=base_card)
        left += 80


data = app.mc.get("npc_data")
df = pd.DataFrame(data)

X = []
Y = []
for d in data:
    features = {
        # "effectiveness": d["effectiveness"],
        **d["move"],
        **d["opponent"],
        **d["user"],
    }
    # Convert the effectiveness value into a discrete label
    if d["effectiveness"] > 0.5:
        label = "effective"
    else:
        label = "ineffective"

    X.append(features)
    Y.append(label)

from sklearn.feature_extraction import DictVectorizer

vec = DictVectorizer()
X = vec.fit_transform(X)

# X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)

# # Split the data into training and test sets
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# # Normalize the data
# scaler = StandardScaler()
# X_train = scaler.fit_transform(X_train)
# X_test = scaler.transform(X_test)

# Train a machine learning model
model = RandomForestClassifier()
model.fit(X, Y)

# Test the model on the test set
# # accuracy = model.score(X_test, Y_test)
# print(f"Test set accuracy: {accuracy:.2f}")


def predict_best_move(moves, opponent_name):
    # Extract the relevant features for each move
    X = []
    for move in moves:
        features = {**move, "opponent_name": opponent_name}
        X.append(features)

    # Convert the list of dictionaries into a numerical format using DictVectorizer
    vec = DictVectorizer()
    X = vec.fit_transform(X)

    # Use the trained machine learning model to make predictions on the list of moves
    predictions = model.predict(X)

    # Find the index of the move with the highest predicted effectiveness
    best_move_index = np.argmax(predictions)
    return moves[best_move_index]


@app.post("/predict_best_move")
def predict_best_move(moves: List[Dict], opponent_name: str):
    # Extract the relevant features for each move
    X = []
    for move in moves:
        features = {**move, "opponent_name": opponent_name}
        X.append(features)

    # Convert the list of dictionaries into a numerical format using DictVectorizer
    vec = DictVectorizer()
    X = vec.fit_transform(X)

    # Use the trained machine learning model to make predictions on the list of moves
    predictions = model.predict(X)

    # Find the index of the move with the highest predicted effectiveness
    best_move_index = np.argmax(predictions)

    # Return the move with the highest predicted effectiveness
    return moves[best_move_index]


# # Define the "choose_move" endpoint
# @app.post("/choose_move")
# def choose_move(pokemon: str, move_names: str):
#     # Predict the effectiveness of each move
#     pokemon = orjson.loads(pokemon)
#     move_names = orjson.loads(move_names)
#     move_predictions = {}
#     for move_name in move_names:
#         move = {"move": move_name}
#         move_prediction = predict_effective_move(pokemon, move)
#         move_predictions[move_name] = move_prediction

#     # Return the move with the highest predicted effectiveness
#     best_move = max(move_predictions, key=move_predictions.get)
#     return best_move


@app.post("/build_team_preview")
def build_team_preview(player1_data: str, player2_data: str):
    """Paramater payload will be like the following
    player1_data: dictionary
        Contains the JSON serializable information for Player 1 containing name & list of (pokemon_sprite_path, level)
    player2_data: dictionary
        Contains the JSON serializable information for Player 2 containing name & list of (pokemon_sprite_path, level)
    """
    player1_data, player2_data = orjson.loads(player1_data), orjson.loads(player2_data)
    player1_pokes = player1_data["pokemon_info"]
    player2_pokes = player2_data["pokemon_info"]

    with Image.open(str(DIR / "team_preview.jpg")).convert("RGBA") as bg:
        draw_player_headers(bg, [player1_data["name"], player2_data["name"]])
        draw_player_teams(bg, player1_pokes, player2_pokes)

        fp = io.BytesIO()
        bg.save(fp, format="PNG")
    fp.seek(0)
    return StreamingResponse(fp, media_type="image/png")


@app.get("/ping")
def ping():
    return {"message": "ping"}


@app.post("/build")
def build_image(
    poke1_image_url: str,
    poke2_image_url: str,
    poke1: str,
    poke2: str,
    background_number: int,
    weather: str,
    trick_room: int,
):
    """Paramater payload will be like the following

    poke1_image_url: str
        URL to poke1 image
    poke2_image_url: str
        URL to poke2 image
    poke1: dictionary
        Contains the JSON serializable information for Pokemon 1
    poke2: dictionary
        Contains the JSON serializable information for Pokemon 2
    background_number: int
        The number of background to use
    weather: str
        The current weather
    trick_room: bool/int
        If a trick room is active
    """
    args = {
        "poke1_image_url": poke1_image_url,
        "poke2_image_url": poke2_image_url,
        "poke1": poke1,
        "poke2": poke2,
        "background_number": background_number,
        "weather": weather,
        "trick_room": trick_room,
    }
    poke1 = orjson.loads(args["poke1"])
    poke2 = orjson.loads(args["poke2"])

    with Image.open(str(DIR / f"bg{args['background_number']}.png")) as bg:

        if int(args["trick_room"]):
            trick_room = PRELOADED["trick_room"].resize(bg.size)
            trick_room.putalpha(128)
            bg.paste(trick_room)

        if args["weather"]:
            w = args["weather"]
            if w in ("rain", "h-rain"):
                layer = PRELOADED["rain"].resize(bg.size)
                bg.paste(layer, mask=layer)
            elif w == "hail":
                layer = PRELOADED["hail"].resize(bg.size)
                bg.paste(layer, mask=layer)
            elif w in ("sun", "h-sun"):
                layer = PRELOADED["sun"].resize(bg.size)
                bg.paste(layer, mask=layer)
            elif w == "sandstorm":
                layer = PRELOADED["sandstorm"].resize(bg.size)
                bg.paste(layer, mask=layer)
            # TODO: wind

        if bg.size != (1280, 640):
            bg = bg.resize((1280, 640), Image.ANTIALIAS)

        try:
            p1 = Image.open(DIR / args["poke1_image_url"]).convert("RGBA")
        except FileNotFoundError:
            print(f"{args['poke1_image_url']} does not exist in duel resources!")
            p1 = Image.open(DIR / "sprites" / "ERROR.png").convert("RGBA")

        try:
            p2 = Image.open(DIR / args["poke2_image_url"]).convert("RGBA")
        except FileNotFoundError:
            print(f"{args['poke2_image_url']} does not exist in duel resources!")
            p2 = Image.open(DIR / "sprites" / "ERROR.png").convert("RGBA")

        p1 = sresize(p1)
        p2 = sresize(p2)

        area = (630, 50)
        bg.paste(p2, area, p2)
        if poke2["substitute"] > 0:
            bg.paste(PRELOADED["sub"], area, mask=PRELOADED["sub"])

        area = (70, 50)
        bg.paste(p1, area, p1)
        p1.close()
        p2.close()

        if poke1["substitute"] > 0:
            bg.paste(PRELOADED["sub"], area, mask=PRELOADED["sub"])

        hb = HealthBar()
        bar1 = hb.bar(math.ceil(poke1["hp"]), poke1["starting_hp"])
        bar2 = hb.bar(math.ceil(poke2["hp"]), poke2["starting_hp"])
        bg.paste(bar1, (86, 44), mask=bar1)
        bg.paste(bar2, (707, 44), mask=bar2)

        fp = io.BytesIO()
        bg.save(fp, "PNG")

    fp.seek(0)
    return StreamingResponse(fp, media_type="image/png")
