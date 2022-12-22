import discord
from discord.ext import commands

import asyncio
import aiohttp
import random
import time
import traceback
import collections
import pandas as pd

from pymemcache.client import base
from pymemcache import serde
from datetime import datetime, timedelta

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from .pokemon import DuelPokemon
from .trainer import MemberTrainer, NPCTrainer
from .battle import Battle
from .buttons import DuelAcceptView, BattleTowerAcceptView
from .data import generate_team_preview

import os

DATE_FORMAT = "%m/%d/%Y, %H:%M:%S"
PREGAME_GIFS = [
    "https://www.demilked.com/magazine/wp-content/uploads/2016/06/gif-animations-replace-loading-screen-3.gif",
    "https://i.imgur.com/yRCJ26G.gif",
    "https://i.redd.it/g63bz0lruoz01.gif",
    "https://cdn.discordapp.com/attachments/637668172367003694/760537617720148028/ezgif-4-4420d991c1fc.gif",
]


class Duel(commands.Cog):
    """Fight pokemon in a duel."""

    def __init__(self, bot):
        self.bot = bot
        self.duel_reset_time = None
        self.init_task = asyncio.create_task(self.initialize())

        self.games = {}
        # TODO: swap this to db
        self.ranks = {}

        self.bt_queue = collections.deque()
        self.mc = base.Client(('178.28.0.20', 11211), serde=serde.PickleSerde(pickle_version=2))

    async def initialize(self):
        """Preps the redis cache."""
        # This is to make sure the duelcooldowns dict exists before we access in the cog check
        await self.bot.redis_manager.redis.execute(
            "HMSET", "duelcooldowns", "examplekey", "examplevalue"
        )
        # And then the 50 per day
        await self.bot.redis_manager.redis.execute(
            "HMSET", "dailyduelcooldowns", "examplekey", "examplevalue"
        )
        self.duel_reset_time = await self.bot.redis_manager.redis.execute(
            "GET", "duelcooldownreset"
        )
        if self.duel_reset_time is None:
            self.duel_reset_time = datetime.now()
            await self.bot.redis_manager.redis.execute(
                "SET", "duelcooldownreset", self.duel_reset_time.strftime(DATE_FORMAT)
            )
        else:
            self.duel_reset_time = datetime.strptime(
                self.duel_reset_time.decode("utf-8"), DATE_FORMAT
            )

    @commands.hybrid_command()
    async def battle_tower_diag(self, ctx):
        """Diagnose Battle Tower"""
        await ctx.send(f"Current Queue: {self.bt_queue}\n\n\nRanks: {self.ranks}")

    @commands.Cog.listener()
    async def on_ready(self):

        """Starts the matchmaking loop when the bot is ready"""
        
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Check if there are enough users in the queue to start a match
            if len(self.bt_queue) >= 2:
                # Matchmake the first two users in the queue
                ctx1 = self.bt_queue.popleft()[1]
                ctx2 = self.bt_queue.popleft()[1]
                await self._initiate_battle_tower(ctx1, ctx2)
            # Wait for 10 seconds before checking the queue again
            await asyncio.sleep(10)

    @staticmethod
    async def _get_opponent(ctx, opponent: discord.Member, battle_type: str):
        """Confirms acceptence of the duel with the requested member."""
        if opponent.id == ctx.author.id:
            await ctx.send("You cannot duel yourself!")
            return False
        return await DuelAcceptView(ctx, opponent, battle_type).wait()

    @staticmethod
    async def _get_battle_tower_opponent(ctx1, ctx2, battle_type: str):
        """Confirms acceptence of battle tower duel with the matched user."""
        if ctx1.author.id == ctx2.author.id:
            await ctx1.send("You cannot duel yourself!")
            await ctx2.send("You cannot duel yuzzef!")
            return False
        return await BattleTowerAcceptView(ctx1, ctx2, battle_type).wait()

    async def _check_cooldowns(self, ctx, opponent: discord.Member):
        """Checks daily cooldowns to see if the author can duel."""
        # Funky neuro code I am going to assume works flawlessly
        # TODO: This seems to only check that ctx.author hasn't dueled 50 times,
        #      should it also check opponent?
        perms = ctx.channel.permissions_for(ctx.guild.me)
        if not all((perms.send_messages, perms.embed_links, perms.attach_files)):
            try:
                await ctx.send(
                    "I need `send_messages`, `embed_links`, and `attach_files` perms in order to let you duel!"
                )
            except discord.HTTPException:
                pass
            return False
        try:
            duel_reset = (
                await self.bot.redis_manager.redis.execute(
                    "HMGET", "duelcooldowns", str(ctx.author.id)
                )
            )[0]

            if duel_reset is None:
                duel_reset = 0
            else:
                duel_reset = float(duel_reset.decode("utf-8"))

            if duel_reset > time.time():
                reset_in = duel_reset - time.time()
                cooldown = f"{round(reset_in)}s"
                await ctx.channel.send(f"Command on cooldown for {cooldown}")
                return
            await self.bot.redis_manager.redis.execute(
                "HMSET", "duelcooldowns", str(ctx.author.id), str(time.time() + 20)
            )
            return True
        except Exception as e:
            ctx.bot.logger.exception("Error in check for duel/commands.py", exc_info=e)
        if datetime.now() > (timedelta(seconds=5) + self.duel_reset_time):
            temp_time = (
                await self.bot.redis_manager.redis.execute("GET", "duelcooldownreset")
            ).decode("utf-8")
            if self.duel_reset_time.strftime(DATE_FORMAT) == temp_time:
                self.duel_reset_time = datetime.now()
                await self.bot.redis_manager.redis.execute(
                    "SET",
                    "duelcooldownreset",
                    self.duel_reset_time.strftime(DATE_FORMAT),
                )
                await self.bot.redis_manager.redis.execute("DEL", "dailyduelcooldowns")
                await self.bot.redis_manager.redis.execute(
                    "HSET", "dailyduelcooldowns", str(ctx.author.id), "0"
                )
                used = 0
            else:
                self.duel_reset_time = datetime.strptime(temp_time, DATE_FORMAT)
                used = await self.bot.redis_manager.redis.execute(
                    "HGET", "dailyduelcooldowns", str(ctx.author.id)
                )
                if used is None:
                    await self.bot.redis_manager.redis.execute(
                        "HSET", "dailyduelcooldowns", str(ctx.author.id), "0"
                    )
                    used = 0
        else:
            used = await self.bot.redis_manager.redis.execute(
                "HGET", "dailyduelcooldowns", str(ctx.author.id)
            )
            if used is None:
                await self.bot.redis_manager.redis.execute(
                    "HSET", "dailyduelcooldowns", str(ctx.author.id), "0"
                )
                used = 0

        used = int(used)

        if used >= 50:
            await ctx.send("You have hit the maximum number of duels per day!")
            return False

        await self.bot.redis_manager.redis.execute(
            "HMSET", "dailyduelcooldowns", str(ctx.author.id), str(used + 1)
        )
        return True

    async def wrapped_run(self, battle):
        """
        Runs the provided battle, handling any errors that are raised.

        Returns the output of the battle, or None if the battle errored.
        """
        winner = None
        duel_start = datetime.now()

        try:
            winner = await battle.run()
        except (aiohttp.client_exceptions.ClientOSError, asyncio.TimeoutError) as e:
            raise e
            await battle.send(
                "The bot encountered an unexpected network issue, "
                "and the duel could not continue. "
                "Please try again in a few moments.\n"
                "Note: Do not report this as a bug."
            )
        except Exception as e:
            await battle.send(
                "`The duel encountered an error.\n`"
                f"Your error code is **`{battle.ctx.interaction.id}`**.\n"
                "Please post this code in <#1009276416656941196> with "
                "details about what was happening when this error occurred."
            )

            def paginate(text: str):
                """Paginates arbatrary length text."""
                last = 0
                pages = []
                for curr in range(0, len(text), 1900):
                    pages.append(text[last:curr])
                    last = curr
                pages.append(text[last : len(text)])
                pages = list(filter(lambda a: a != "", pages))
                return pages

            stack = "".join(traceback.TracebackException.from_exception(e).format())
            pages = paginate(stack)
            for idx, page in enumerate(pages):
                if idx == 0:
                    page = f"Exception ID {battle.ctx._interaction.id}\n\n" + page
                await self.bot.get_partial_messageable(998290393709944842).send(
                    f"```py\n{page}\n```"
                )
            self.games[int(battle.ctx._interaction.id)] = battle

        if battle.trainer1.is_human() and battle.trainer2.is_human():
            t1 = battle.trainer1
            t2 = battle.trainer2
            # async with self.bot.db[0].acquire() as pconn:
            #     for _ in range(2):
            #         cases = await pconn.fetch(
            #             f"SELECT time, extract(epoch from time)::integer as time2, args FROM skylog WHERE u_id = $1 AND time > $2 AND args LIKE '%mock%{t2.id}%'",
            #             t1.id,
            #             duel_start - timedelta(minutes=30),
            #         )
            #         if cases:
            #             ommitted = max(0, len(cases) - 10)
            #             desc = (
            #                 f"**<@{t1.id}> MAY BE CHEATING IN DUELS!**\n"
            #                 f"Dueled with <@{t2.id}> at <t:{int(duel_start.timestamp())}:F> and ran the following commands:\n\n"
            #             )
            #             for r in cases[:10]:
            #                 desc += f"<t:{r['time2']}:F>\n`{r['args']}`\n\n"
            #             if ommitted:
            #                 desc += f"Plus {ommitted} ommitted commands.\n"
            #             desc += "Check `skylog` for more information."
            #             embed = discord.Embed(title="ALERT", description=desc, color=0xDD1111)
            #             await self.bot.get_partial_messageable(550751484694888469).send(embed=embed)
            #         # Swap who to check in an easy way
            #         t1, t2 = t2, t1

        return winner

    @commands.hybrid_command()
    async def train(self, ctx):
        data = self.mc.get("npc_data")
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
        self.bot.npc_model = RandomForestClassifier()
        self.bot.npc_model.fit(X, Y)
        await ctx.send("Model training complete!")

    @commands.hybrid_group()
    async def duel(self, ctx):
        """Initiate a 1v1 duel, 6v6 battle, NPC duel or an Inverse duel."""
        ...

    @duel.command()
    async def tower(self, ctx):
        """A battle tower duel."""
        await ctx.send("Coming soon...")
        return
        e = discord.Embed(
            title="Adding you to the matchmaking queue...",
            description="Please wait",
            color=0xFFB6C1,
        )
        msg = await ctx.send(embed=e)

        if any([x[0] == ctx.author.id for x in self.bt_queue]):
            e.title = "You are already in the queue, please wait..."
            e.description = ""
            await msg.edit(embed=e)
            return

        self.bt_queue.append([ctx.author.id, ctx])

        e.title = "Added to the queue, waiting for a match!..."
        e.description = ""
        await asyncio.sleep(3)
        await msg.edit(embed=e)

        # Now we have added a user to the queue,

    async def _initiate_battle_tower(self, ctx1, ctx2):
        if not await self._get_battle_tower_opponent(ctx1, ctx2, "battle tower duel"):
            return

        e = discord.Embed(
            title="Pokemon Battle accepted! Loading...",
            description="Please wait",
            color=0xFFB6C1,
        )
        e.set_image(url=random.choice(PREGAME_GIFS))
        [await ctx.send(embed=e) for ctx in [ctx1, ctx2]]
        # await ctx.send(embed=e)

        if not await self._check_cooldowns(ctx1, ctx2.author):
            return

        async with ctx1.bot.db[0].acquire() as pconn:
            challenger1 = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx1.author.id,
            )
            challenger2 = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx2.author.id,
            )
        if challenger1 is None:
            [
                await ctx.send(
                    f"{ctx1.author.name} has not selected a Pokemon!\nSelect one with `/select <id>` first!"
                )
                for ctx in [ctx1, ctx2]
            ]
            # await ctx.send(f"{ctx.author.name} has not selected a Pokemon!\nSelect one with `/select <id>` first!")
            return
        if challenger2 is None:
            [
                await ctx.send(
                    f"{ctx2.author.name} has not selected a Pokemon!\nSelect one with `/select <id>` first!"
                )
                for ctx in [ctx1, ctx2]
            ]
            # await ctx.send(f"{opponent.name} has not selected a Pokemon!\nSelect one with `/select <id>` first!")
            return
        if challenger1["pokname"].lower() == "egg":
            [
                await ctx.send(
                    f"{ctx1.author.name} has an egg selected!\nSelect a different pokemon with `/select <id>` first!"
                )
                for ctx in [ctx1, ctx2]
            ]
            # await ctx.send(f"{ctx.author.name} has an egg selected!\nSelect a different pokemon with `/select <id>` first!")
            return
        if challenger2["pokname"].lower() == "egg":
            [
                await ctx.send(
                    f"{ctx2.author.name} has an egg selected!\nSelect a different pokemon with `/select <id>` first!"
                )
                for ctx in [ctx1, ctx2]
            ]
            # await ctx.send(f"{opponent.name} has an egg selected!\nSelect a different pokemon with `/select <id>` first!")
            return

        # Gets a Pokemon object based on the specifics of each poke
        p1_current = await DuelPokemon.create(ctx1, challenger1)
        p2_current = await DuelPokemon.create(ctx2, challenger2)
        owner1 = MemberTrainer(ctx1.author, [p1_current])
        owner2 = MemberTrainer(ctx2.author, [p2_current])
        battle = Battle([ctx1, ctx2], Battle.BATTLE_TOWER, owner1, owner2)
        winner = await self.wrapped_run(battle)

        if winner is None:
            return

        # Update missions progress
        user = await ctx1.bot.mongo_find(
            "users",
            {"user": winner.id},
            default={"user": winner.id, "progress": {}},
        )
        progress = user["progress"]
        progress["duel-win"] = progress.get("duel-win", 0) + 1
        await ctx1.bot.mongo_update(
            "users", {"user": winner.id}, {"progress": progress}
        )

        # Grant xp
        desc = ""
        async with ctx1.bot.db[0].acquire() as pconn:
            for poke in winner.party:
                # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                data = await pconn.fetchrow(
                    "SELECT hitem, exp FROM pokes WHERE id = $1", poke.id
                )
                held_item = data["hitem"].lower()
                current_exp = data["exp"]
                exp = 0
                if held_item != "xp-block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky-egg":
                        exp *= 2.5
                    # Max int for the exp col
                    exp = min(int(exp), 2147483647 - current_exp)
                    desc += f"{poke._starting_name} got {exp} exp from winning.\n"
                await pconn.execute(
                    "UPDATE pokes SET happiness = happiness + 1, exp = exp + $1 WHERE id = $2",
                    exp,
                    poke.id,
                )
        if desc:
            [
                await ctx.send(embed=discord.Embed(description=desc, color=0xFFB6C1))
                for ctx in [ctx1, ctx2]
            ]

    @duel.command()
    async def single(self, ctx, opponent: discord.Member):
        """A 1v1 duel with another user's selected pokemon."""
        if not await self._get_opponent(ctx, opponent, "one pokemon duel"):
            return

        e = discord.Embed(
            title="Pokemon Battle accepted! Loading...",
            description="Please wait",
            color=0xFFB6C1,
        )
        e.set_image(url=random.choice(PREGAME_GIFS))
        await ctx.send(embed=e)

        if not await self._check_cooldowns(ctx, opponent):
            return

        async with ctx.bot.db[0].acquire() as pconn:
            challenger1 = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx.author.id,
            )
            challenger2 = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                opponent.id,
            )
        if challenger1 is None:
            await ctx.send(
                f"{ctx.author.name} has not selected a Pokemon!\nSelect one with `/select <id>` first!"
            )
            return
        if challenger2 is None:
            await ctx.send(
                f"{opponent.name} has not selected a Pokemon!\nSelect one with `/select <id>` first!"
            )
            return
        if challenger1["pokname"].lower() == "egg":
            await ctx.send(
                f"{ctx.author.name} has an egg selected!\nSelect a different pokemon with `/select <id>` first!"
            )
            return
        if challenger2["pokname"].lower() == "egg":
            await ctx.send(
                f"{opponent.name} has an egg selected!\nSelect a different pokemon with `/select <id>` first!"
            )
            return

        # Gets a Pokemon object based on the specifics of each poke
        p1_current = await DuelPokemon.create(ctx, challenger1)
        p2_current = await DuelPokemon.create(ctx, challenger2)
        owner1 = MemberTrainer(ctx.author, [p1_current])
        owner2 = MemberTrainer(opponent, [p2_current])

        battle = Battle(ctx, Battle.DUEL, owner1, owner2)
        winner = await self.wrapped_run(battle)

        if winner is None:
            return

        # Update missions progress
        user = await ctx.bot.mongo_find(
            "users",
            {"user": winner.id},
            default={"user": winner.id, "progress": {}},
        )
        progress = user["progress"]
        progress["duel-win"] = progress.get("duel-win", 0) + 1
        await ctx.bot.mongo_update("users", {"user": winner.id}, {"progress": progress})

        # Grant xp
        desc = ""
        async with ctx.bot.db[0].acquire() as pconn:
            for poke in winner.party:
                # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                data = await pconn.fetchrow(
                    "SELECT hitem, exp FROM pokes WHERE id = $1", poke.id
                )
                held_item = data["hitem"].lower()
                current_exp = data["exp"]
                exp = 0
                if held_item != "xp-block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky-egg":
                        exp *= 2.5
                    # Max int for the exp col
                    exp = min(int(exp), 2147483647 - current_exp)
                    desc += f"{poke._starting_name} got {exp} exp from winning.\n"
                await pconn.execute(
                    "UPDATE pokes SET happiness = happiness + 1, exp = exp + $1 WHERE id = $2",
                    exp,
                    poke.id,
                )
        if desc:
            await ctx.send(embed=discord.Embed(description=desc, color=0xFFB6C1))

    @duel.command()
    async def party(self, ctx, opponent: discord.Member):
        """A 6v6 duel with another user's selected party."""
        await self.run_party_duel(ctx, opponent)

    @duel.command()
    async def inverse(self, ctx, opponent: discord.Member):
        """A 6v6 inverse battle with another user's selected party."""
        await self.run_party_duel(ctx, opponent, inverse_battle=True)

    async def run_party_duel(self, ctx, opponent, *, inverse_battle=False):
        """Creates and runs a party duel."""
        battle_type = "party duel"
        if inverse_battle:
            battle_type += " in the **inverse battle ruleset**"
        if not await self._get_opponent(ctx, opponent, battle_type):
            return

        # e = discord.Embed(
        #     title="Pokemon Battle accepted! Loading...",
        #     description="Please wait",
        #     color=0xFFB6C1,
        # )
        # e.set_image(url=random.choice(PREGAME_GIFS))
        # await ctx.send(embed=e)

        if not await self._check_cooldowns(ctx, opponent):
            return

        async with ctx.bot.db[0].acquire() as pconn:
            party1 = await pconn.fetchval(
                "SELECT party FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if party1 is None:
                await ctx.send(
                    f"{ctx.author.name} has not Started!\nStart with `/start` first!"
                )
                return
            party1 = [x for x in party1 if x != 0]
            raw1 = await pconn.fetch("SELECT * FROM pokes WHERE id = any($1)", party1)
            raw1 = list(filter(lambda e: e["pokname"] != "Egg", raw1))
            raw1.sort(key=lambda e: party1.index(e["id"]))
            party2 = await pconn.fetchval(
                "SELECT party FROM users WHERE u_id = $1",
                opponent.id,
            )
            if party2 is None:
                await ctx.send(
                    f"{opponent.name} has not Started!\nStart with `/start` first!"
                )
                return
            party2 = [x for x in party2 if x != 0]
            raw2 = await pconn.fetch("SELECT * FROM pokes WHERE id = any($1)", party2)
            raw2 = list(filter(lambda e: e["pokname"] != "Egg", raw2))
            raw2.sort(key=lambda e: party2.index(e["id"]))

        if not raw1:
            await ctx.send(
                f"{ctx.author.name} has no pokemon in their party!\nAdd some with `/party` first!"
            )
            return
        if not raw2:
            await ctx.send(
                f"{opponent.name} has no pokemon in their party!\nAdd some with `/party` first!"
            )
            return

        # Gets a Pokemon object based on the specifics of each poke
        pokes1 = []
        for pdata in raw1:
            poke = await DuelPokemon.create(ctx, pdata)
            pokes1.append(poke)
        pokes2 = []
        for pdata in raw2:
            poke = await DuelPokemon.create(ctx, pdata)
            pokes2.append(poke)
        owner1 = MemberTrainer(ctx.author, pokes1)
        owner2 = MemberTrainer(opponent, pokes2)

        battle = Battle(ctx, Battle.PARTY_DUEL, owner1, owner2, inverse_battle=inverse_battle)

        battle.trainer1.event.clear()
        battle.trainer2.event.clear()
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()

        winner = await self.wrapped_run(battle)

        if winner is None:
            return

        # Update mission progress
        user = await ctx.bot.mongo_find(
            "users",
            {"user": winner.id},
            default={"user": winner.id, "progress": {}},
        )
        progress = user["progress"]
        progress["duel-win"] = progress.get("duel-win", 0) + 1
        await ctx.bot.mongo_update("users", {"user": winner.id}, {"progress": progress})

        # Grant xp
        desc = ""
        async with ctx.bot.db[0].acquire() as pconn:
            for poke in winner.party:
                if poke.hp == 0 or not poke.ever_sent_out:
                    continue
                # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                data = await pconn.fetchrow(
                    "SELECT hitem, exp FROM pokes WHERE id = $1", poke.id
                )
                held_item = data["hitem"].lower()
                current_exp = data["exp"]
                exp = 0
                if held_item != "xp-block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky-egg":
                        exp *= 2.5
                    # Max int for the exp col
                    exp = min(int(exp), 2147483647 - current_exp)
                    desc += f"{poke._starting_name} got {exp} exp from winning.\n"
                await pconn.execute(
                    "UPDATE pokes SET happiness = happiness + 1, exp = exp + $1 WHERE id = $2",
                    exp,
                    poke.id,
                )
        if desc:
            await ctx.send(embed=discord.Embed(description=desc, color=0xFFB6C1))

    @duel.command()
    async def npc(self, ctx):
        """A 1v1 duel with an npc AI."""
        # TODO: remove this
        ENERGY_IMMUNE = False

        async with ctx.bot.db[0].acquire() as pconn:
            # Reduce energy
            data = await pconn.fetchrow(
                "SELECT energy, inventory::json FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if data is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return

            challenger1 = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx.author.id,
            )
            if challenger1 is None:
                await ctx.send(
                    f"{ctx.author.mention} has not selected a Pokemon!\nSelect one with `/select <id>` first!"
                )
                return
            if challenger1["pokname"].lower() == "egg":
                await ctx.send(
                    f"{ctx.author.mention} has an egg selected!\nSelect a different pokemon with `/select <id>` first!"
                )
                return

            if data["energy"] <= 0:
                await ctx.send("You don't have energy left!")
                cog = ctx.bot.get_cog("Extras")
                await cog.vote.callback(cog, ctx)
                return
            elif ctx.channel.id == 998291646443704320:
                ENERGY_IMMUNE = True
            else:
                await pconn.execute(
                    "UPDATE users SET energy = energy - 1 WHERE u_id = $1",
                    ctx.author.id,
                )

            npc_pokemon = await pconn.fetch(
                (
                    "SELECT * FROM pokes WHERE pokelevel BETWEEN $1 - 10 AND $1 + 10 and not 'tackle' = ANY(moves) "
                    "AND atkiv <= 31 AND defiv <= 31 AND spatkiv <= 31 AND spdefiv <= 31 AND speediv <= 31 AND hpiv <= 31 "
                    "ORDER BY id DESC LIMIT 1000"
                ),
                challenger1["pokelevel"],
            )
            challenger2 = dict(random.choice(npc_pokemon))
            challenger2["poknick"] = "None"

        # Gets a Pokemon object based on the specifics of each poke
        p1_current = await DuelPokemon.create(ctx, challenger1)
        p2_current = await DuelPokemon.create(ctx, challenger2)
        owner1 = MemberTrainer(ctx.author, [p1_current])
        owner2 = NPCTrainer(ctx.bot, [p2_current])

        battle = Battle(ctx, Battle.NPC, owner1, owner2)
        winner = await self.wrapped_run(battle)

        if winner is not owner1:
            return
        if ENERGY_IMMUNE:
            return

        battle_multi = data["inventory"].get("battle-multiplier", 1)

        # Update mission progress
        user = await ctx.bot.mongo_find(
            "users",
            {"user": ctx.author.id},
            default={"user": ctx.author.id, "progress": {}},
        )
        progress = user["progress"]
        progress["npc-win"] = progress.get("npc-win", 0) + 1
        await ctx.bot.mongo_update(
            "users", {"user": ctx.author.id}, {"progress": progress}
        )

        # Grant credits & xp
        creds = random.randint(100, 600)
        creds *= min(battle_multi, 50)
        desc = f"You received {creds} credits for winning the duel!\n\n"
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                creds,
                ctx.author.id,
            )
            for poke in winner.party:
                # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                data = await pconn.fetchrow(
                    "SELECT hitem, exp FROM pokes WHERE id = $1", poke.id
                )
                held_item = data["hitem"].lower()
                current_exp = data["exp"]
                exp = 0
                if held_item != "xp-block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky-egg":
                        exp *= 2.5
                    # Max int for the exp col
                    exp = min(int(exp), 2147483647 - current_exp)
                    desc += f"{poke._starting_name} got {exp} exp from winning.\n"
                await pconn.execute(
                    "UPDATE pokes SET happiness = happiness + 1, exp = exp + $1 WHERE id = $2",
                    exp,
                    poke.id,
                )
        desc += f"\nConsider joining the [Official Mewbot Server]({'https://discord.gg/mewbot'}) if you are a fan of pokemon duels!\n"
        await ctx.send(embed=discord.Embed(description=desc, color=0xFFB6C1))

    async def update_ranks(self, ctx, winner: discord.Member, loser: discord.Member):
        """
        Updates the ranks between two members, based on the result of the match.

        https://en.wikipedia.org/wiki/Elo_rating_system#Theory
        """
        # This is the MAX amount of ELO that can be swapped in any particular match.
        # Matches between players of the same rank will transfer half this amount.
        # TODO: dynamically update this based on # of games played, rank, and whether the duel participants were random.
        K = 50

        R1 = self.ranks.get(winner.id, 1000)
        R2 = self.ranks.get(loser.id, 1000)

        E1 = 1 / (1 + (10 ** ((R2 - R1) / 400)))
        E2 = 1 / (1 + (10 ** ((R1 - R2) / 400)))

        # If tieing is added, this needs to be the score of each player
        S1 = 1
        S2 = 0

        newR1 = round(R1 + K * (S1 - E1))
        newR2 = round(R2 + K * (S2 - E2))

        self.ranks[winner.id] = newR1
        self.ranks[loser.id] = newR2
        msg = "**__Rank Adjustments__**\n"
        msg += f"**{winner.name}**: {R1} -> {newR1} ({newR1-R1:+})\n"
        msg += f"**{loser.name}**: {R2} -> {newR2} ({newR2-R2:+})"
        await ctx.send(msg)
