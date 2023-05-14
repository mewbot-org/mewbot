import pprint
from fastapi.responses import RedirectResponse, PlainTextResponse, ORJSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Request, Header
from pydantic import BaseModel
from decimal import Decimal
import contextlib
import datetime
import aioredis
import asyncio
import uvicorn
import aiohttp
import orjson
import asyncpg
import secrets
import random
import json
import os

# import stripe
import time
import traceback
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

REDEEMS_PER_DOLLAR = 1
CREDITS_PER_DOLLAR = 2000

app = FastAPI()

home = str(Path.home())
os.chdir(f"{home}/mewbot/callbacks/src")
load_dotenv("../../env/bot.env")
load_dotenv("../../env/mongo.env")
load_dotenv("../../env/postgres.env")
load_dotenv("../../env/voting.env")
load_dotenv("../../env/discord.env")

TOKEN = os.environ["MTOKEN"]
DATABASE = os.environ["DATABASE_URL"]
MONGO_URL = os.environ["MONGO_URL"]
DONATOR_ROLE = int(os.environ["DONATOR_ROLE"])

# stripe.api_key = 'sk_test_51H74m0ITgsMlv29LgTV87yS7qD8crcWHdKgFMDlAYLD1VaMDVbAYrv5dO0Mvqzhuoq7oOf3fd2ZviH9MOPC0gbiU0098wGhOTo'
botlist_tokens = {
    "discordbotlist.com": os.environ["DBL"],
    "topgg": os.environ["TOPGGVERIFY"],
    "rdl": os.environ["RDL_TOKEN"],
}
STREAKS = {
    10: {
        "gems": 3,
        "chest": None,
        "skin": False,
    },
    15: {
        "gems": 3,
        "chest": None,
        "skin": False,
    },
    20: {
        "gems": 5,
        "chest": None,
        "skin": False,
    },
    25: {
        "gems": 3,
        "chest": "rare_chest",
        "skin": False,
    },
    30: {
        "gems": 5,
        "chest": None,
        "skin": False,
    },
    35: {
        "gems": 3,
        "chest": "mythic_chest",
        "skin": False,
    },
    40: {
        "gems": 5,
        "chest": "mythic_chest",
        "skin": False,
    },
    45: {
        "gems": 0,
        "chest": "legend_chest",
        "skin": False,
    },
    50: {
        "gems": 7,
        "chest": None,
        "skin": False,
    },
    60: {
        "gems": 7,
        "chest": None,
        "skin": False,
    },
    70: {
        "gems": 5,
        "chest": "legend_chest",
        "skin": False,
    },
    80: {
        "gems": 10,
        "chest": None,
        "skin": False,
    },
    90: {
        "gems": 10,
        "chest": "legend_chest",
        "skin": False,
    },
    100: {
        "gems": 0,
        "chest": None,
        "skin": True,
    },
}


class AppUtils:
    def __init__(self):
        self.bot_token = TOKEN
        self.app = app
        self.session = aiohttp.ClientSession()
        self.base_channel_url = (
            "https://discordapp.com/api/v6/channels/{channel_id}/messages"
        )
        self.request_header = {
            "Authorization": f"Bot {self.bot_token}",
            "User-Agent": "DiscordBot (https://github.com/Rapptz/discord.py 2.0.0a) Python/3.8 aiohttp/3.7.4.post0",
            "Content-Type": "application/json",
        }

        try:
            with open("/code/shop.json", "r") as f:
                self.SHOP = json.load(f)
        except FileNotFoundError:
            with open("shop.json", "r") as f:
                self.SHOP = json.load(f)
        self.berryList = {
            "aguav_seed",
            "figy_seed",
            "iapapa_seed",
            "mago_seed",
            "wiki_seed",
            "sitrus_seed",
        }

    async def post_request(self, base_url, data):
        r = await self.session.post(base_url, headers=self.request_header, json=data)
        r.raise_for_status()
        return r

    async def put_request(self, base_url):
        r = await self.session.put(base_url, headers=self.request_header)
        r.raise_for_status()
        return r

    async def get_dm_id(self, user_id):
        base_url = "https://discordapp.com/api/v6/users/@me/channels"
        data = {
            "recipient_id": user_id,
        }
        response = await self.post_request(base_url, data)
        response = await response.json()
        return response["id"]

    async def send_message(self, channel_id, amount, credits):
        data = {
            "embed": {
                "title": "Thank You For Supporting Mewbot!",
                "description": (
                    f"You have received {amount} Redeems and {credits} Credits for supporting "
                    "Mewbot!\nYou can use your redeems with `/redeem <pokemon_name>` to get any "
                    "Pokemon of your choice!"
                ),
                "color": 0xFFB6C1,
            }
        }
        await self.post_request(
            self.base_channel_url.format(channel_id=channel_id), data
        )

    async def send_vote_message(self, channel_id, votes, reward):
        data = {
            "embed": {
                "title": f"Vote streak {votes}x!",
                "description": (
                    f"Thanks for voting! On top of your usual rewards, you also got {reward}.\n"
                    "Keep voting every day for even better rewards!"
                ),
                "color": 0xFFB6C1,
            }
        }
        try:
            await self.post_request(
                self.base_channel_url.format(channel_id=channel_id), data
            )
        except Exception:
            pass

    async def send_skin_message(self, u_id):
        data = {
            "embed": {
                "title": f"Vote streak skin",
                "description": (
                    f"`{u_id}` has reached the custom skin vote streak reward!"
                ),
                "color": 0xFFB6C1,
            }
        }
        try:
            await self.post_request(
                self.base_channel_url.format(channel_id=998563289082626049), data
            )
        except Exception:
            pass

    async def send_warn_message(self, user_id: int, data: dict):
        if user_id:
            data = {
                "content": f"<@473541068378341376> <@790722073248661525> User {user_id} attempted to fake a PayPal transaction.  Transaction ID: {data['txn_id']}"
            }
        else:
            data = {
                "content": f"<@473541068378341376> <@790722073248661525> An unknown user attempted to fake a PayPal transaction.  Transaction ID: {data['txn_id']}"
            }
        await self.post_request(
            self.base_channel_url.format(channel_id=998563289082626049), data
        )

    async def send_topgg_log_message(self, user_id: int):
        if user_id:
            data = {"content": f"{user_id}"}
        try:
            await self.post_request(
                self.base_channel_url.format(channel_id=998563289082626049), data
            )
        except Exception as e:
            tb = "".join(traceback.TracebackException.from_exception(e).format())
            print(tb)

    async def give_donator_role(self, user_id, role):
        base_url = (
            f"https://discordapp.com/api/v6/guilds/{os.environ['OFFICIAL_SERVER']}"
            f"/members/{user_id}/roles/{role}"
        )
        await self.put_request(base_url)

    async def give_redeems(self, user_id, amount, ref):
        redeems = amount * REDEEMS_PER_DOLLAR
        credits = amount * CREDITS_PER_DOLLAR
        async with self.app.pool.acquire() as pconn:
            query = """INSERT INTO donations (u_id, amount, txn_id)
            VALUES ($1, $2, $3)"""
            args = (user_id, amount, ref)
            print("Sending Redeems...")
            await pconn.execute(query, *args)
            await pconn.execute(
                (
                    "UPDATE users SET redeems = redeems + $1, mewcoins = mewcoins + $2 "
                    "WHERE u_id = $3"
                ),
                redeems,
                credits,
                user_id,
            )

        print(f"{user_id} paid {amount} $")

        role = DONATOR_ROLE
        with contextlib.suppress(Exception):
            dm_id = await self.get_dm_id(user_id)
            await self.give_donator_role(user_id, role)
            await self.send_message(dm_id, redeems, credits)

    async def mongo_find(self, collection, query, default=None):
        result = await self.app.mongo[collection].find_one(query)
        if not result:
            return default
        return result

    async def mongo_update(self, collection, filter, update):
        result = await self.app.mongo[collection].find_one(filter)
        if not result:
            await self.app.mongo[collection].insert_one({**filter, **update})
        await self.app.mongo[collection].update_one(filter, {"$set": update})


class AuthUtils:
    _PROTECTED_TYPES = (
        type(None),
        int,
        float,
        Decimal,
        datetime.datetime,
        datetime.date,
        datetime.time,
    )

    @staticmethod
    def is_protected_type(obj):
        """
        Determine if the object instance is of a protected type.

        Objects of protected types are preserved as-is when passed to
        force_str(strings_only=True).
        """
        return isinstance(obj, AuthUtils._PROTECTED_TYPES)

    @staticmethod
    def force_bytes(s, encoding="utf-8", strings_only=False, errors="strict"):
        """
        From Django:

            Similar to smart_bytes, except that lazy instances are resolved to
            strings, rather than kept as lazy objects.
            If strings_only is True, don't convert (some) non-string-like objects.
        """
        # Handle the common case first for performance reasons.
        if isinstance(s, bytes):
            if encoding == "utf-8":
                return s
            else:
                return s.decode("utf-8", errors).encode(encoding, errors)
        if strings_only and AuthUtils.is_protected_type(s):
            return s
        if isinstance(s, memoryview):
            return bytes(s)
        return str(s).encode(encoding, errors)

    @staticmethod
    def secure_strcmp(val1, val2):
        """
        From Django:

        Return True if the two strings are equal, False otherwise securely.
        """
        return secrets.compare_digest(
            AuthUtils.force_bytes(val1), AuthUtils.force_bytes(val2)
        )


# For now they use the same format, but we'll use multiple basemodels
class FatesVote(BaseModel):
    id: str


class DBLVote(BaseModel):
    id: str


def is_donation(data):
    return (
        "payment_status" in data
        and data["payment_status"] == "Completed"
        and "-" not in data.get("payment_gross", data.get("mc_gross"))
    )


def is_test_donation(data):
    return (
        "payment_status" in data
        and data["payment_status"] == "Completed"
        and "test_ipn" in data
    )


def is_new_case(data):
    return "txn_type" in data and data["txn_type"] == "new_case"


def is_chargeback(data):
    return "mc_gross" in data and "-" in data["mc_gross"]


def is_recurring(data):
    return "txn_type" in data and data["txn_type"] == "recurring_payment"


async def verify_ipn(data):
    params = {k: v for k, v in data.items()}
    params["cmd"] = "_notify-validate"

    if "test_ipn" in data and str(data["test_ipn"]) == "1":
        url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    else:
        url = "https://ipnpb.paypal.com/cgi-bin/webscr"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mewbot IPN Verifier",
    }

    async with app.utils.session.get(url, params=params, headers=headers) as resp:
        body = await resp.text()
        if body == "INVALID":
            user_id = int(data["custom"]) if data["custom"].isdigit() else None
            await app.utils.send_warn_message(user_id, params)
            return True
        elif body == "VERIFIED":
            print("Transaction Verified")
            return True
        else:
            return resp


@app.on_event("startup")
async def startup():
    async def init(con):
        await con.set_type_codec(
            typename="json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )

    app.pool = await asyncpg.create_pool(DATABASE, init=init)
    app.mongo = AsyncIOMotorClient(MONGO_URL).pokemon
    app.redis = await aioredis.create_pool(
        "redis://178.28.0.13", minsize=10, maxsize=20
    )
    app.utils = AppUtils()
    print("Pool has been Created Successfully!")


@app.on_event("shutdown")
async def shutdown():
    await app.pool.close()
    await app.utils.session.close()

    app.redis.close()
    await app.redis.wait_closed()


# Stripe is no longer used
# @app.post("/create_stripe_checkout")
# async def create_stripe_checkout(request: Request):
#    data = await request.form()
#    data = {k: v for k, v in data.items()}
#    print(data)
#    session = stripe.checkout.Session.create(
#        payment_method_types = ['card', 'ideal', 'sofort'],
#        line_items = [
#            {
#                'amount': 1 * 100,
#                'currency': 'EUR',
#                'name': data['item_name'],
#                'quantity': data['amount'],
#            }
#        ],
#        mode = 'payment',
#        success_url = 'https://www.mewbot.xyz/thankyou.html',
#        cancel_url = 'https://www.mewbot.xyz/donate',
#        metadata = {'custom': data['custom']}
#    )
#    print(session.url)
#    return PlainTextResponse(session.url)


@app.post("/paypal/")
@app.post("/paypal")
async def paypalhook(request: Request):
    data = await request.form()
    print("Requester - ", request.client.host)
    if is_donation(data):
        data = {k: v for k, v in data.items()}

        pprint.pprint(data)

        # Check to make sure the paypal transaction was valid
        # Paypal is shit: https://www.paypal-community.com/t5/Sandbox-Environment/IPN-listener-getting-status-other-than-VERIFIED-or-INVALID/td-p/1850590
        # We'll try three times to see if paypal will spontaneously work
        for _ in range(3):
            result = await verify_ipn(data)
            if result in [True, False]:
                break
            await asyncio.sleep(5)

        if not (result is True):
            if result is False:
                return PlainTextResponse("")
            else:
                print("I failed to decode IPN verifier request.")
                print(result.status)
                print(await result.text())

        if is_recurring(data):
            data["custom"] = data["transaction_subject"].split("+")[-1]

        if "custom" not in data or not data["custom"].isdigit():
            print("No custom set, throwing out transaction.")
            return PlainTextResponse("")

        if "payment_gross" in data or "mc_gross" in data:
            user_id = int(data["custom"])
            amount = int(data.get("payment_gross", data.get("mc_gross")).split(".")[0])
        else:
            user_id = int(data["user_id"])
            amount = int(data["amount"].split(".")[0])
        await app.utils.give_redeems(user_id, amount, data["txn_id"] + "_PP")
    elif is_test_donation(data):
        print("Test donation...")
        amount = int(data["payment_gross"].split(".")[0])
        if data["custom"].isdigit():
            user_id = int(data["custom"])
        else:
            user_id = 790722073248661525
        await app.utils.give_redeems(user_id, amount, data["txn_id"] + "_PP")
    """
    elif is_new_case(data):
        print("New Case")
        await appeal_dispute(data['case_id'])
    elif is_chargeback(data):
        print("Charged Back")
        id = int(data["custom"])
        async with app.pool.acquire() as pconn:
            await pconn.execute(
                "UPDATE botbans SET users = array_append(users, $1) WHERE id = 1;", id
            )
            await report_to_dylee(
                await get_dm_id(id),
                f"You have charged back ${data['mc_gross']}, You have 48 Hours to Reverse this or risk a dispute with PayPal (MewBot, getting our money back) + Getting your account disabled.",
            )
            await report_to_dylee(await get_dm_id(455277032625012737), f"{id} has Charged Back!")
            return "", 200
            pokes = await pconn.fetchval("SELECT pokes FROM users WHERE u_id = $1", id)
            await pconn.execute(f"DELETE FROM pokes WHERE id = ANY ( $1 )", pokes)
            await pconn.execute(
                "UPDATE botbans SET users = array_append(users, $1) WHERE id = 1", id
            )
            await pconn.execute("DELETE FROM users WHERE u_id = $1", id)
    """
    return PlainTextResponse("")


@app.get("/paystack_verify/{ref}")
async def paystack_verify(ref: int, request: Request):
    headers = {
        "Authorization": "Bearer sk_live_30eec7a16fc9d0e331e809c1bf2b11625b75ec9e",
    }

    base_url = f"https://api.paystack.co/transaction/verify/{ref}"
    async with aiohttp.request(
        "GET",
        base_url,
        headers=headers,
    ) as r:
        r.raise_for_status()
        data = (await r.json())["data"]

    amount = int(data["amount"] / 100 / 500)
    user_id = int(data["metadata"]["custom"])

    await app.utils.give_redeems(user_id, amount, f"{ref}_PV")

    return RedirectResponse(url="https://mewbot.xyz/donate/thankyou.html")


# top.gg
@app.post("/hooks/topgg")
async def votes_topgg(request: Request):
    try:
        data = await request.json()
        auth = request.headers.get("Authorization")
        user_id = int(data["user"])
        return await vote_handler(data, auth, user_id, "topgg")
    except Exception as e:
        tb = "".join(traceback.TracebackException.from_exception(e).format())
        print(tb)
        return PlainTextResponse("")


# discordbotlist
@app.post("/hooks/discordbotlist")
async def votes_dbl(request: Request):
    try:
        data = await request.json()
        auth = request.headers.get("Authorization")
        user_id = int(data["id"])
        return await vote_handler(data, auth, user_id, "discordbotlist.com")
    except Exception as e:
        tb = "".join(traceback.TracebackException.from_exception(e).format())
        print(tb)
        return PlainTextResponse("")


# rdl
@app.post("/hooks/rdl")
async def votes_rdl(request: Request):
    return PlainTextResponse("")
    try:
        data = await request.json()
        auth = request.headers.get("Authorization")
        user_id = int(data["user"]["id"])
        return await vote_handler(data, auth, user_id, "rdl")
    except Exception as e:
        tb = "".join(traceback.TracebackException.from_exception(e).format())
        print(tb)
        return PlainTextResponse("")


async def vote_handler(data, auth, user_id, list_name):
    """Function to handle all votes from all current and new lists."""

    # Handle auth first
    if not AuthUtils.secure_strcmp(auth, str(botlist_tokens.get(list_name))):
        return PlainTextResponse("", status_code=401)  # Invalid auth

    print(f"Processing vote from {list_name} for {user_id}...")

    # TEMP LOGGING TOPGG
    if list_name == "topgg":
        await app.utils.send_topgg_log_message(user_id)

    # if user_id == 473541068378341376:
    #    votes = await app.redis.get(f"voting-{user_id}")
    #    if votes is None:
    #        votes = 0
    #    else:
    #        votes = int(votes)
    #    if votes >= 2:
    #        return PlainTextResponse("")
    #    if votes == 0:
    #        await app.redis.setex(f"voting-{user_id}", datetime.timedelta(hours=12), 1)
    #    else:
    #        await app.redis.incr(f"voting-{user-id}")
    berry_chance = random.randint(1, 30)
    berry = None
    cheaps = [t["item"] for t in app.utils.SHOP if t["price"] <= 8000]
    expensives = [
        t["item"] for t in app.utils.SHOP if t["price"] >= 5000 and t["price"] <= 8000
    ]
    if berry_chance <= 1:
        berry = random.choice(expensives)
    elif berry_chance <= 4:
        berry = random.choice(cheaps)
    elif berry_chance <= 12:
        berry = random.choice(list(app.utils.berryList))
    if berry:
        async with app.pool.acquire() as pconn:
            #Old bag system w/JSON array
            #items = await pconn.fetchval(
                #"SELECT items::json FROM users WHERE u_id = $1", user_id
            #)
            #if items is not None:
                #items[berry] = items.get(berry, 0) + 1
                #await pconn.execute(
                    #"UPDATE users SET items = $1::json WHERE u_id = $2",
                    #items,
                    #user_id,
                #)
            query = f"UPDATE bag SET {berry} = {berry} + 1 WHERE u_id = $1"
            args = (user_id)
            await pconn.execute(query, args)

    async with app.pool.acquire() as pconn:
        await pconn.execute(
            f"UPDATE users SET mewcoins = mewcoins + 1500, upvotepoints = upvotepoints + 1, energy = LEAST(energy + 5, 15) WHERE u_id = $1",
            user_id,
        )
        if list_name == "topgg":
            data = await pconn.fetchrow(
                "SELECT last_vote, vote_streak, skins::json FROM users WHERE u_id = $1",
                user_id,
            )
            if data is None:
                return PlainTextResponse("")
            if data["last_vote"] < time.time() - (36 * 60 * 60):
                vote_streak = 1
            else:
                vote_streak = data["vote_streak"] + 1
            await pconn.execute(
                "UPDATE users SET last_vote = $1, vote_streak = $2 WHERE u_id = $3",
                int(time.time()),
                vote_streak,
                user_id,
            )
            #inventory = data["inventory"]
            skins = data["skins"]
            # different than vote_streak for it to wrap around while displaying as the correct #
            reward_value = ((vote_streak - 1) % 100) + 1
            if reward_value in STREAKS:
                reward = STREAKS[reward_value]
                msg = ""
                if reward["gems"]:
                    await pconn.execute(
                        "UPDATE account_bound SET radiant_gem = radiant_gem + $1 WHERE u_id = $2",
                        reward["gems"],
                        user_id
                    )
                    msg += f"-**{reward['gems']}x** radiant gems\n"
                if reward["chest"]:
                    chest_name = reward["chest"]
                    await pconn.execute(
                        f"UPDATE account_bound SET {chest_name} = {chest_name} + 1 WHERE u_id = $1",
                        user_id
                    )
                    msg += f"-A **{reward['chest']} chest**\n"
                if reward["skin"]:
                    # await app.utils.send_skin_message(user_id)
                    skin = random.choice(
                        [("mewtwo", "vote"), ("mewtwo", "vote2"), ("mewtwo", "vote3")]
                    )
                    msg += f"-An **exclusive {skin[0].title()} skin** for voting! See `/skin` for more information.\n"
                    # TODO: replace with default dict?
                    if skin[0] not in skins:
                        skins[skin[0]] = {}
                    if skin[1] not in skins[skin[0]]:
                        skins[skin[0]][skin[1]] = 1
                    else:
                        skins[skin[0]][skin[1]] += 1
                await pconn.execute(
                    "UPDATE users SET skins = $1::json WHERE u_id = $2",
                    skins,
                    user_id,
                )
                dm_id = await app.utils.get_dm_id(user_id)
                await app.utils.send_vote_message(dm_id, vote_streak, msg)
    user = await app.utils.mongo_find(
        "users",
        {"user": user_id},
        default={"user": user_id, "progress": {}},
    )
    progress = user["progress"]
    progress["upvote"] = progress.get("upvote", 0) + 1
    await app.utils.mongo_update("users", {"user": user_id}, {"progress": progress})
    return PlainTextResponse("")


@app.get("/")
async def index():
    return {"hello": "world"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=15211)
