import discord
from discord.ext import commands

import asyncio
import aiohttp
import random
import time
import traceback
import collections
import pandas as pd
import joblib

from pymemcache.client import base
from pymemcache import serde
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from mewutils.misc import STAFFSERVER, get_generation, get_badge_emoji
from mewcogs.achieve import threshold_check

from .pokemon import DuelPokemon
from .trainer import MemberTrainer, NPCTrainer
from .battle import Battle
from .buttons import DuelAcceptView, BattleTowerAcceptView
from .data import generate_team_preview
from .npc import generate_pokemon, trainers

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

    # This is for duel achievements.
    async def check_duel_requirements(
        self,
        new_count: int,
        current_count: int = 0,
        achievement: str = None,
        channel: int = None,
    ):
        # Checks threshold and rewards appropriate achievement
        achieve_lvl, msg, level_up = threshold_check(new_count, current_count)
        if level_up:
            achievement_msg = achievement.replace("_", " ").title()
            embed = discord.Embed(
                title="⭐ Achievement Complete!",
                description=f"Congrats! {msg} in the {achievement_msg} Achievement. 🎊",
                color=0x0084FD,
            )
            await channel.send(embed=embed)
            return

    # @commands.hybrid_command()
    async def battle_tower_diag(self, ctx):
        """Diagnose Battle Tower"""
        await ctx.send(f"Current Queue: {self.bt_queue}\n\n\nRanks: {self.ranks}")

    # @commands.Cog.listener()
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
        patreon_status = await ctx.bot.patreon_tier(ctx.author.id)
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
                "HMSET",
                "duelcooldowns",
                str(ctx.author.id),
                str(
                    time.time()
                    + 15
                    - (15 * 0.5 if patreon_status == "Ace Trainer" else 0)
                ),
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
                    page = f"Exception ID {battle.ctx.interaction.id}\n\n" + page
            await self.bot.get_partial_messageable(998290948863836160).send(
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

    async def update_ranks(
        self, ctx, winner: discord.Member, loser: discord.Member, forfeit: bool
    ):
        """
        Updates the ranks between two members, based on the result of the match.

        https://en.wikipedia.org/wiki/Elo_rating_system#Theory
        """
        # This is the MAX amount of ELO that can be swapped in any particular match.
        # Matches between players of the same rank will transfer half this amount.
        # TODO: dynamically update this based on # of games played, rank, and whether the duel participants were random.
        winner_K, loser_K = [50, 50]
        if forfeit is not None:
            winner_K = 15
            loser_k = 200

        # Original example, used self.ranks saved within class.
        # Completed todo and moved to db. Left for reference.
        # R1 = self.ranks.get(winner.id, 1000)
        # R2 = self.ranks.get(loser.id, 1000)

        # Have to pull ranks from database for both players
        # Value should have a default of 1000 in database
        async with ctx.bot.db[0].acquire() as pconn:
            R1 = await pconn.fetchval(
                "SELECT rank FROM users WHERE u_id = $1", winner.id
            )
            R2 = await pconn.fetchval(
                "SELECT rank FROM users WHERE u_id = $1", loser.id
            )

            # This calc was left the same as example
            E1 = 1 / (1 + (10 ** ((R2 - R1) / 400)))
            E2 = 1 / (1 + (10 ** ((R1 - R2) / 400)))

            # If tieing is added, this needs to be the score of each player
            # 12/8/23 - Was not added so we will these this as is.
            S1 = 1
            S2 = 0

            newR1 = round(R1 + winner_K * (S1 - E1))
            newR2 = round(R2 + loser_K * (S2 - E2))

            # This was here for reference, moved to db code below
            # self.ranks[winner.id] = newR1
            # self.ranks[loser.id] = newR2

            # Update rankings in the database
            if newR1 < 0:
                newR1 = 0
            if newR2 < 0:
                newR2 = 0
            await pconn.execute(
                "UPDATE users SET rank = $1 WHERE u_id = $2", newR1, winner.id
            )
            await pconn.execute(
                "UPDATE users SET rank = $1 WHERE u_id = $2", newR2, loser.id
            )

        msg = f"**{winner.name}**: {R1} -> {newR1} ({newR1-R1:+})\n"
        msg += f"**{loser.name}**: {R2} -> {newR2} ({newR2-R2:+})"
        return msg

    # @commands.hybrid_command()
    async def train(self, ctx):
        data = (await ctx.bot.db[1].npc_data.find_one())["npc_data"]
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
        joblib.dump(self.bot.npc_model, "npc_model.pkl")
        await ctx.send("Model training complete!")

    @commands.hybrid_group()
    async def duel(self, ctx):
        """Initiate a 1v1 duel, 6v6 battle, NPC duel or an Inverse duel."""
        ...

    # @duel.command()
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
                if held_item != "xp_block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky_egg":
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
                if held_item != "xp_block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky_egg":
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

    @duel.command()
    # @discord.app_commands.guilds(STAFFSERVER)
    async def ranked(self, ctx, opponent: discord.Member):
        """A 6v6 ranked duel with another user's party."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Coming Soon")
        # return
        if ctx.guild.id != 1271229684998475807:
            await ctx.send(
                "You can only use this command in the Trainer District Server."
            )
            return
        await self.run_ranked_duel(ctx, opponent)

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

        battle = Battle(
            ctx, Battle.PARTY_DUEL, owner1, owner2, inverse_battle=inverse_battle
        )

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
                if held_item != "xp_block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky_egg":
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

    async def run_ranked_duel(self, ctx, opponent, *, inverse_battle=False):
        """Creates and runs a ranked duel."""
        battle_type = "party duel"
        # At the moment ranked does not support inverse battles
        # if inverse_battle:
        # battle_type += " in the **inverse battle ruleset**"
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

        battle = Battle(
            ctx, Battle.RANKED, owner1, owner2, inverse_battle=inverse_battle
        )

        battle.trainer1.event.clear()
        battle.trainer2.event.clear()
        preview_view = await generate_team_preview(battle)
        await battle.trainer1.event.wait()
        await battle.trainer2.event.wait()
        preview_view.stop()

        winner = await self.wrapped_run(battle)

        if winner is None:
            return
        if type(winner) == list:
            forfeit = winner[1]
            winner = winner[0]
        else:
            forfeit = False
            winner = winner

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
                if held_item != "xp_block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky_egg":
                        exp *= 2.5
                    # Max int for the exp col
                    exp = min(int(exp), 2147483647 - current_exp)
                    desc += f"{poke._starting_name} got {exp} exp from winning.\n"
                await pconn.execute(
                    "UPDATE pokes SET happiness = happiness + 1, exp = exp + $1 WHERE id = $2",
                    exp,
                    poke.id,
                )
        embed = discord.Embed(title="Duel Over", color=0xFFB6C1)
        if desc:
            embed.add_field(name="Pokemon Details", value=f"{desc}", inline=False)
        # Prepare loser
        # If winner issued challenged
        if winner.id == ctx.author.id:
            loser = opponent
        else:
            loser = ctx.author
        msg = await self.update_ranks(ctx, winner, loser, forfeit)
        embed.add_field(name="Rank Adjustments", value=f"{msg}", inline=False)
        await ctx.send(embed=embed)

    # Everything from here below is for NPC Duels
    @duel.command()
    async def npc(self, ctx, leader: str = None):
        """Duel a NPC Pokemon or Gym Leader"""
        # TODO: remove this
        ENERGY_IMMUNE = False
        if not await self._check_cooldowns(ctx, opponent=ctx.author.id):
            return

        async with ctx.bot.db[0].acquire() as pconn:
            # Reduce energy
            user_data = await pconn.fetchrow(
                "SELECT npc_energy, region, win_streak, party, exp_share, selected FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if user_data is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return

            if user_data["npc_energy"] <= 0:
                await ctx.send("You don't have energy left!")
                cog = ctx.bot.get_cog("Extras")
                await cog.vote.callback(cog, ctx)
                return
            elif ctx.channel.id == 998291646443704320:
                ENERGY_IMMUNE = True
            else:
                patreon = await ctx.bot.patreon_tier(ctx.author.id)
                if patreon == "Ace Trainer" and random.random() < 0.5:
                    pass
                else:
                    await pconn.execute(
                        "UPDATE users SET npc_energy = npc_energy - 1 WHERE u_id = $1",
                        ctx.author.id,
                    )

        # Now that things are checked for energy
        # Use the correct duel type
        if leader is None:
            await self.run_npc_single(ctx, user_data)
        else:
            await self.run_npc_party(ctx, leader, user_data)

    # Player vs NPC Single Duel
    async def run_npc_single(self, ctx, user_data):
        async with ctx.bot.db[0].acquire() as pconn:
            region = user_data["region"]
            selected = user_data["selected"]

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

            # Going to generate player's pokemon first
            # That way Pokemon are deformed and demega'd
            # Gets a Pokemon object based on the specifics of each poke
            p1_current = await DuelPokemon.create(ctx, challenger1)

            patreon = await ctx.bot.patreon_tier(ctx.author.id)
            if (
                patreon
                in (
                    "Ace Trainer",
                    "Elite Collector",
                    "Rarity Hunter",
                    "Crystal Tier",
                    "Silver Tier",
                    "Yellow Tier",
                    "Red Tier",
                )
                or ctx.guild.id != 998128574898896906
            ):
                poke_data = await ctx.bot.db[1].pfile.find_one(
                    {"identifier": p1_current._name.lower()}
                )
                try:
                    generation_id = poke_data["generation_id"]
                except TypeError:
                    generation_id = random.randint(1, 9)
                if random.randint(1, 100) <= 50:
                    npc_choices = (
                        await ctx.bot.db[1]
                        .pfile.find(
                            {
                                "$and": [
                                    {"generation_id": generation_id},
                                    {"evolved_from_species_id": {"$ne": "null"}},
                                ]
                            }
                        )
                        .to_list(None)
                    )
                else:
                    npc_choices = (
                        await ctx.bot.db[1]
                        .pfile.find(
                            {
                                "$and": [
                                    {"generation_id": generation_id},
                                    {"evolved_from_species_id": None},
                                ]
                            }
                        )
                        .to_list(None)
                    )
                pokemon = random.choice(npc_choices)
                npc_name = pokemon["identifier"].lower()
                # If ditto pick a new Pokemon
                if npc_name == "ditto":
                    npc_data = random.choice(npc_choices)
                    npc_name = npc_data["identifier"].lower()
                challenger2 = await generate_pokemon(
                    ctx, npc_name, challenger1["pokname"], challenger1["pokelevel"]
                )
            else:
                npc_pokemon = await pconn.fetch(
                    (
                        "SELECT * FROM pokes WHERE pokelevel BETWEEN $1 - 10 AND $1 + 10 and not 'tackle' = ANY(moves) "
                        "AND atkiv <= 31 AND defiv <= 31 AND spatkiv <= 31 AND spdefiv <= 31 AND speediv <= 31 AND hpiv <= 31 "
                        "ORDER BY id DESC LIMIT 1000"
                    ),
                    challenger1["pokelevel"],
                )
                challenger2 = dict(random.choice(npc_pokemon))

                # If Eternatus-eternamax pick another Pokemon
                if challenger2["pokname"] == "Eternatus-eternamax":
                    challenger2 = dict(random.choice(npc_pokemon))
                challenger2["poknick"] = "None"

        npc_trainer = random.choice(trainers)
        # Gets a Pokemon object based on the specifics of each poke
        p2_current = await DuelPokemon.create(ctx, challenger2)
        owner1 = MemberTrainer(ctx.author, [p1_current])
        owner2 = NPCTrainer(npc_trainer, [p2_current])

        battle = Battle(ctx, Battle.NPC, owner1, owner2)
        winner = await self.wrapped_run(battle)
        won = True

        if winner == "forfeit":
            await ctx.bot.db[0].execute(
                "UPDATE users SET win_streak = 0 WHERE u_id = $1", ctx.author.id
            )
            embed = discord.Embed(
                title="You Lost!",
                description=(
                    "Your win streak has been reset!\n"
                    "No credit gain due to not hitting the 5 turn minimum!"
                ),
            )
            await ctx.send(embed=embed)
            return
        elif winner is not owner1:
            won = False
            embed = discord.Embed(
                title="You Lost!", description="Your win streak has been reset!"
            )
        else:
            embed = discord.Embed(
                title="You Won!", description="Your win streak has been increased by 1!"
            )

        async with ctx.bot.db[0].acquire() as pconn:
            battle_multi = await pconn.fetchval(
                "SELECT battle_multiplier FROM account_bound WHERE u_id = $1",
                ctx.author.id,
            )
            if battle_multi is None:
                battle_multi = 1

        if won:
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
        creds = random.randint(200, 300)
        creds *= min(battle_multi, 50)
        creds = round(creds)

        async with ctx.bot.db[0].acquire() as pconn:
            if won == False:
                creds //= 2  # * (.25 if random.random() < .65 else .35))
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                    creds,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE users SET win_streak = 0 WHERE u_id = $1", ctx.author.id
                )
                party_msg = ""
            else:
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                    creds,
                    ctx.author.id,
                )
                party_msg = ""
                for poke in winner.party:
                    # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                    data = await pconn.fetchrow(
                        "SELECT hitem, exp, pokname FROM pokes WHERE id = $1", poke.id
                    )
                    held_item = data["hitem"].lower()
                    current_exp = data["exp"]
                    poke_name = data["pokname"].capitalize()
                    happiness = random.randint(1, 3)
                    exp = 0
                    if held_item != "xp_block":
                        exp = (150 * poke.level) / 7
                        if held_item == "lucky_egg":
                            exp *= 2.5
                        # Max int for the exp col
                        exp = min(int(exp), 2147483647 - current_exp)
                    party_msg += f"`{poke_name}` has gained **{exp}** and **{happiness}** happiness!\n"
                    await pconn.execute(
                        "UPDATE pokes SET happiness = happiness + $1, exp = exp + $2 WHERE id = $3",
                        happiness,
                        exp,
                        poke.id,
                    )
                await pconn.execute(
                    "UPDATE users SET win_streak = win_streak + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await pconn.execute(
                    f"UPDATE achievements SET ai_single_wins = ai_single_wins + 1 WHERE u_id = $1",
                    ctx.author.id,
                )

        embed.add_field(
            name="Rewards", value=f"You've gained **{creds}** credits!", inline=False
        )
        embed.add_field(name="Pokemon Party", value=f"{party_msg}", inline=False)
        embed.set_footer(
            text=f"Losing causes credit loss and streak reset!\nConsider joining the Mewbot Official for player run gyms!"
        )
        await ctx.send(embed=embed)
        # desc += f"\nConsider joining the [Official Mewbot Server]({'https://discord.gg/mewbot'}) if you are a fan of pokemon duels!\n"
        # await ctx.send(embed=discord.Embed(description=desc, color=0xFFB6C1))

    # Player VS NPC Party Duel
    async def run_npc_party(self, ctx, npc, user_data):
        """Creates and runs a party duel."""
        # patreon = await ctx.bot.patreon_tier(ctx.author.id)
        # patreon not in ("Crystal Tier", "Silver Tier", "Yellow Tier", "Red Tier") or ctx.guild.id != 998128574898896906:
        # await ctx.send("Coming soon!")
        # return

        async with ctx.bot.db[0].acquire() as pconn:
            user_data = await pconn.fetchrow(
                "SELECT region, win_streak, party, exp_share FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            battle_multi = await pconn.fetchval(
                "SELECT battle_multiplier FROM account_bound"
            )
            if user_data is None:
                await ctx.send(
                    f"{ctx.author.name} has not Started!\nChoose your starter with `/start` first!"
                )
                return
            region = user_data["region"]
            win_streak = user_data["win_streak"]
            party1 = user_data["party"]
            exp_share = user_data["exp_share"]

            # Grab badge data
            badge_data = await pconn.fetchrow(
                "SELECT * FROM achievements WHERE u_id = $1", ctx.author.id
            )
            if not badge_data:
                await pconn.execute(
                "INSERT INTO achievements (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    ctx.author.id,
                )
                badge_data = {}
            badge_data = dict(badge_data)

            # TODO: Decide whether we're doing Badge Levels OR Level 50 Rule
            # As of 11/7 server wants to do Level 50 Rule.
            # badge_level = get_badge_level(badge_data, region)

            # Here we ensure leader exists and then check player can challenge
            leader_data = await ctx.bot.db[1].gym_leaders.find_one(
                {"$and": [{"identifier": npc.lower()}, {"region": region}]}
            )
            party2 = leader_data["party"]
            streak_requirement = leader_data["requirement"]

            # Check Gym Leader Party exists
            if party2 is None:
                await ctx.send(
                    f"Couldn't pull data for that Gym Leader, please report in Onixian Official."
                )
                return
            # Reject if Win Streak isn't hit
            if win_streak < streak_requirement:
                if ctx.author.id == 334155028170407949:
                    pass
                else:
                    await ctx.send(
                        f"Sorry you need a win streak of {streak_requirement} to challenge Gym Leader {npc.capitalize()}"
                    )
                    return

            # Format Player's Data
            party1 = [x for x in party1 if x != 0]
            raw1 = await pconn.fetch("SELECT * FROM pokes WHERE id = any($1)", party1)

            # Adding Generation Check
            # If Pokemon's Gen doesn't match Leader , denies Pokemon
            for pokemon in raw1:
                # Un-Mega Pokemon
                pname = pokemon["pokname"].lower()
                if pname.endswith("-mega-x") or pname.endswith("-mega-y"):
                    pname = pname[:-7]
                if pname.endswith("-mega"):
                    pname = pname[:-5]

                # Pull data from MongoDB
                form_info = await self.bot.db[1].forms.find_one({"identifier": pname})
                pokemon_info = await self.bot.db[1].pfile.find_one(
                    {"id": form_info["pokemon_id"]}
                )
                try:
                    if pokemon_info["generation_id"] > leader_data["generation"]:
                        await ctx.send(
                            f"Sorry Trainer, your {pname.title()} doesn't match the generation of this Gym Leader!"
                        )
                        return
                except TypeError:
                    ctx.bot.logger.info(f"POKE ERRORED: {pokemon_info}")

            raw1 = list(filter(lambda e: e["pokname"] != "Egg", raw1))
            raw1.sort(key=lambda e: party1.index(e["id"]))

            # Format NPC's Data
            party2 = [x for x in party2 if x != 0]
            raw2 = await pconn.fetch(
                "SELECT * FROM leader_pokemon WHERE id = any($1)", party2
            )
            raw2 = list(filter(lambda e: e["pokname"] != "Egg", raw2))
            raw2.sort(key=lambda e: party2.index(e["id"]))

        if not raw1:
            await ctx.send(
                f"{ctx.author.name} has no pokemon in their party!\nAdd some with `/party add` first!"
            )
            return

        # Gets a Pokemon object based on the specifics of each poke
        # Player Pokemon first , NPC Pokemon second
        pokes1 = []
        for pdata in raw1:
            poke = await DuelPokemon.create(ctx, pdata, True)
            pokes1.append(poke)
        pokes2 = []
        for pdata in raw2:
            poke = await DuelPokemon.create(ctx, pdata, True)
            pokes2.append(poke)

        owner1 = MemberTrainer(ctx.author, pokes1)
        leader_name = f"Gym Leader {leader_data['identifier'].capitalize()}"
        owner2 = NPCTrainer(leader_name, pokes2)

        battle = Battle(ctx, Battle.PARTY_DUEL, owner1, owner2, inverse_battle=False)

        battle.trainer1.event.clear()
        battle.trainer2.event.clear()
        # preview_view = await generate_team_preview(battle)
        # await battle.trainer1.event.wait()
        # await battle.trainer2.event.wait()
        # preview_view.stop()

        winner = await self.wrapped_run(battle)

        # Grant credits & xp
        creds = random.randint(200, 400)
        creds *= min(battle_multi, 50)
        creds = round(creds)  #  * (.25 if random.random() < .65 else .35))
        creds_msg = f"You received **{creds} credits** for winning the duel!\n\n"
        desc = ""
        async with ctx.bot.db[0].acquire() as pconn:
            # Win Streak
            if not winner.is_human():
                await pconn.execute(
                    "UPDATE users SET win_streak = 0 WHERE u_id = $1", ctx.author.id
                )
                embed = discord.Embed(
                    title="You Lost!",
                    description=(
                        "Your win streak has been reset!\n"
                        "No credit gain due to not hitting the 5 turn minimum!"
                    ),
                )
                await ctx.send(embed=embed)
                return
            else:
                await pconn.execute(
                    "UPDATE users SET win_streak = win_streak + 1 WHERE u_id = $1",
                    ctx.author.id,
                )

            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1, win_streak = win_streak + 1 WHERE u_id = $2",
                creds,
                winner.id,
            )
            if exp_share is True:
                # They have an exp share , apply to whole party
                for poke in winner.party:
                    if poke.hp == 0 or not poke.ever_sent_out:
                        continue
                    # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                    data = await pconn.fetchrow(
                        "SELECT pokname, hitem, exp, pokelevel, happiness FROM pokes WHERE id = $1",
                        poke.id,
                    )
                    held_item = data["hitem"].lower()
                    current_exp = data["exp"]
                    level = data["pokelevel"]
                    current_happiness = data["happiness"]
                    name = data["pokname"].title()
                    exp = 0
                    happiness = random.randint(1, 5)
                    if held_item != "xp_block":
                        exp = (200 * level) / 7
                        if held_item == "lucky_egg":
                            exp *= 1.5
                        if held_item == "soothe_bell":
                            happiness *= 0.5
                        if (current_happiness + happiness) <= 255:
                            current_happiness += happiness
                        # Max int for the exp col
                        exp = min(int(exp), 2147483647 - current_exp)
                        desc += f"`{name}` got **{exp} exp** and gained **{happiness} happiness**.\n"
                        await pconn.execute(
                            "UPDATE pokes SET happiness = $1, exp = exp + $2 WHERE id = $3",
                            current_happiness,
                            exp,
                            poke.id,
                        )
            else:
                # Giving exp just to first party pokemon
                poke = winner.party[0]
                # We do a fetch here instead of using poke.held_item as that item *could* be changed over the course of the duel.
                data = await pconn.fetchrow(
                    "SELECT hitem, exp, happiness FROM pokes WHERE id = $1", poke.id
                )
                held_item = data["hitem"].lower()
                current_exp = data["exp"]
                current_happiness = data["happiness"]
                exp = 0
                happiness = random.randint(1, 5)
                if held_item != "xp_block":
                    exp = (150 * poke.level) / 7
                    if held_item == "lucky_egg":
                        exp *= 1.5
                    if held_item == "soothe_bell":
                        happiness *= 0.5
                    if (current_happiness + happiness) <= 255:
                        current_happiness += happiness
                    # Max int for the exp col
                    exp = min(int(exp), 2147483647 - current_exp)
                    desc += f"{poke._starting_name} got {exp} exp from winning.\n"
                    await pconn.execute(
                        "UPDATE pokes SET happiness = $1, exp = exp + $2 WHERE id = $3",
                        current_happiness,
                        exp,
                        poke.id,
                    )

        embed = discord.Embed(
            title="You've Won!",
            description="Here are your rewards...",
        )

        # Give achievement credit
        async with ctx.bot.db[0].acquire() as pconn:
            leaders = (
                await ctx.bot.db[1].gym_leaders.find({"region": region}).to_list(None)
            )
            leaders = [t["column"] for t in leaders]

            # Final Achievement Checks
            if badge_data[leader_data["column"]] != True:
                badge_data[leader_data["column"]] = True
                query = leader_data["query"]
                await pconn.execute(query, ctx.author.id)
                emoji, badge_name = get_badge_emoji(leader_name=leader_data["column"])
                achieve_msg = f"Congrats! You have received the {badge_name.capitalize()} Badge {emoji}!"
            else:
                achieve_msg = None

            # Region complete achievement check
            if badge_data[region] == False:
                checks = []
                for leader in leaders:
                    if badge_data[f"{leader}"] == False:
                        checks.append("False")

                if "False" not in checks:
                    await pconn.execute(
                        f"UPDATE achievements SET {region} = True WHERE u_id = $1",
                        winner.id,
                    )
                    embed.add_field(
                        name="Achievement Unlocked ⭐",
                        value=f"You have beat the {region.title()}!",
                        inline=False,
                    )

            # Achievements for AI Party Wins
            current_count = badge_data["ai_party_wins"]
            new_count = current_count + 1
            await pconn.execute(
                f"UPDATE achievements SET ai_party_wins = $1 WHERE u_id = $2",
                new_count,
                winner.id,
            )
            await self.check_duel_requirements(
                new_count, current_count, "ai_party_wins", ctx.channel
            )
        if achieve_msg:
            embed.add_field(
                name="Badge Unlocked!", value=f"{achieve_msg}", inline=False
            )
        embed.add_field(name="Items", value=f"{creds_msg}", inline=False)
        embed.add_field(name="Pokemon", value=f"{desc}", inline=False)
        await ctx.send(embed=embed)
