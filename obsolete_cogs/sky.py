import inspect
import math
import io
import textwrap
import traceback
import logging
import os
import time
import shlex
import asyncio
import asyncpg
import discord
from discord import Embed
import random
import aiohttp
import aiosmtplib
import pathlib
import ast
from collections import defaultdict
from mewutils.misc import get_pokemon_image, pagify, MenuView, ConfirmView
from mewutils.checks import Rank, check_admin, check_mod, check_helper, check_investigator, check_support, check_gymauth
from mewcore import commondb
import datetime
from copy import copy
from discord.ext import commands, tasks
from discord.ext.commands.view import StringView
from discord.ext.commands.converter import MemberConverter, TextChannelConverter, _convert_to_bool
from pokemon_utils.classes import *
from pokemon_utils.utils import get_pokemon_info
from mewcogs.pokemon_list import *
from mewcogs.pokemon_list import _
from mewcogs.json_files import *
from contextlib import redirect_stdout
from mewcogs.pokemon_list import LegendList
from email.message import EmailMessage




IMG_SERVER_BASE_SKIN = "https://dyleee.github.io/mewbot-images/sprites/skins/"
IMG_SERVER_BASE_RAD = "https://dyleee.github.io/mewbot-images/sprites/radiant/"
SKIN_BASE = "/home/dyroot/mewbot/shared/duel/sprites/skins/"
RAD_BASE = "/home/dyroot/mewbot/shared/duel/sprites/radiant/"

GREEN = "\N{LARGE GREEN CIRCLE}"
YELLOW = "\N{LARGE YELLOW CIRCLE}"
RED = "\N{LARGE RED CIRCLE}"


class Sky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}
        self.safe_edb = ""
        self.cleanup_sessions.start()
        if self.bot.cluster["id"] == 1:
            self.task = asyncio.create_task(self.store_lb())
        else:
            self.task = None

    async def cog_before_invoke(self, ctx):
        ...
        # async with ctx.bot.db[0].acquire() as pconn:
        #     await pconn.execute(
        #         "INSERT INTO skylog (u_id, command, args, jump, time) VALUES ($1, $2, $3, $4, $5)",
        #         ctx.author.id,
        #         ctx.command.qualified_name,
        #         ctx.message.content,
        #         ctx.message.jump_url,
        #         ctx.message.created_at.replace(tzinfo=None),
        #     )

    def cog_unload(self):
        if self.task is not None:
            self.task.cancel()

    async def store_lb(self):
        """Stores leaderboard entries to the 'leaderboard' mongo collection."""
        while True:
            # Sleep until the same time each day
            await asyncio.sleep(86400 - (time.time() % 86400))
            ts = time.time()
            data = {}
            async with self.bot.db[0].acquire() as pconn:
                details = await pconn.fetch(
                    f"""SELECT u_id, cardinality(pokes) as pokenum FROM users ORDER BY pokenum DESC LIMIT 50"""
                )
            pokes = [record["pokenum"] for record in details]
            ids = [record["u_id"] for record in details]
            for idx, id in enumerate(ids):
                pokenum = pokes[idx]
                try:
                    name = (await self.bot.fetch_user(id)).name
                except Exception:
                    name = "?"
                num = idx + 1
                data[id] = {"position": num, "count": pokenum}
                await asyncio.sleep(1)
            data = {"leaderboard": data, "timestamp": ts}
            await self.bot.db[1].leaderboard.insert_one(data)

    @tasks.loop(seconds=60)
    async def cleanup_sessions(self):
        for channel in self.sessions:
            for user in [u for u in self.sessions[channel]]:
                if (time.time() - self.sessions[channel][user]["last"]) >= (60 * 5):
                    del self.sessions[channel][user]
                    c = self.bot.get_channel(channel)
                    await c.send(f"Mock session ended for mocker {user}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.sessions:
            return

        if message.channel.id not in self.sessions:
            return

        entry = None
        try:
            entry = self.sessions[message.channel.id][message.author.id]
        except KeyError:
            return

        if not entry:
            return

        if message.content.startswith(":"):
            self.sessions[message.channel.id][message.author.id]["last"] = time.time()

            msg = copy(message)
            msg.author = entry["mocking"]
            msg.content = ";" + message.content[1:]

            fake_ctx = await self.bot.get_context(msg)
            await self.bot.invoke(fake_ctx)
        elif message.content.startswith("m:"):
            self.sessions[message.channel.id][message.author.id]["last"] = time.time()

            msg = copy(message)
            msg.author = entry["mocking"]
            msg.content = message.content[2:]

            self.bot.dispatch("message", msg)

    async def load_bans_cross_cluster(self):
        launcher_res = await self.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return
        processes = len(launcher_res[0])
        body = "await bot.load_bans()"
        await self.bot.handler(
            "_eval", processes, args={"body": body, "cluster_id": "-1"}, scope="bot", _timeout=10
        )

    @check_mod()
    @commands.hybrid_command()
    async def spcount(self, ctx, userid: discord.Member):
        """MOD: Returns a users special pokemon counts, such as shiny and radiant"""
        async with ctx.bot.db[0].acquire() as pconn:
            shiny = await pconn.fetchval(
                "select count(*) from pokes where shiny = true AND id in (select unnest(u.pokes) from users u where u.u_id = $1)", userid.id
            )
            radiant = await pconn.fetchval(
                "select count(*) from pokes where radiant = true AND id in (select unnest(u.pokes) from users u where u.u_id = $1)", userid.id
            )
        embed = discord.Embed()
        embed.add_field(name="Number of Shiny pokemon", value=f"{shiny}", inline=True)
        embed.add_field(name="Number of Radiant pokemon", value=f"{radiant}", inline=False)
        embed.set_footer(text="Special Pokemon Counts")
        await ctx.send(embed=embed)

    @check_investigator()
    @commands.hybrid_command()
    async def mostcommonchests(self, ctx):
        """Shows the users who have the most common chests in their inv."""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "SELECT u_id, (inventory::json->>'common chest')::int as cc FROM users "
                "WHERE (inventory::json->>'common chest')::int IS NOT NULL ORDER BY cc DESC LIMIT 10"
            )
        result = ""
        for row in data:
            result += f"`{row['u_id']}` - `{row['cc']}`\n"
        await ctx.send(embed=discord.Embed(description=result, color=0xDD00DD))

    @check_investigator()
    @commands.hybrid_command()
    async def donations(self, ctx, userid: discord.Member):
        """INVESTIGATOR: Shows a users total recorded donations from ;donate command only"""
        async with ctx.bot.db[0].acquire() as pconn:
            money = await pconn.fetchval(
                "select sum(amount) from donations where u_id = $1", userid.id
            )
        await ctx.send(money or "0")

    @check_mod()
    @commands.hybrid_command()
    async def whoowns(self, ctx, poke: int):
        """MOD: Shows who owns a specific pokemon by its global ID"""
        async with ctx.typing():
            async with ctx.bot.db[0].acquire() as pconn:
                user = await pconn.fetch("SELECT u_id FROM users WHERE $1 = ANY(pokes)", poke)
                market = await pconn.fetch(
                    "SELECT id FROM market WHERE poke = $1 AND buyer IS NULL", poke
                )
            msg = ""
            if user:
                uids = [str(x["u_id"]) for x in user]
                uids = "\n".join(uids)
                msg += f"Users who own poke `{poke}`:\n```" + uids + "```\n\n"
            if market:
                mids = [str(x["id"]) for x in market]
                mids = "\n".join(mids)
                msg += f"Market listings for poke `{poke}`:\n```" + mids + "```\n\n"
            if not msg:
                await ctx.send(f"Nobody owns poke `{poke}`.")
                return
            await ctx.send(msg[:1999])

    @check_helper()
    @commands.hybrid_command()
    async def marketinfo(self, ctx, market_id: int):
        """HELPER: Hidden info about marketed pokes."""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT poke, owner, price, buyer FROM market WHERE id = $1", market_id
            )
        if not data:
            await ctx.send("That market id does not exist!")
            return
        msg = f"[Market info for listing #{market_id}]\n"
        msg += f"[Poke]  - {data['poke']}\n"
        msg += f"[Owner] - {data['owner']}\n"
        msg += f"[Price] - {data['price']}\n"
        if data["buyer"] is None:
            msg += "[Buyer] - Currently listed\n"
        elif not data["buyer"]:
            msg += "[Buyer] - Removed by owner\n"
        else:
            msg += f"[Buyer] - {data['buyer']}\n"
        msg = f"```ini\n{msg}```"
        await ctx.send(msg)

    @check_admin()
    @commands.hybrid_command()
    async def dupecheck(self, ctx, user_id: discord.Member):
        """ADMIN: Check a user to see if any of their pokemon have more than one owner."""
        async with ctx.typing():
            async with ctx.bot.db[0].acquire() as pconn:
                result = await pconn.fetch(
                    "SELECT pokes.id FROM pokes WHERE pokes.id IN (SELECT unnest(users.pokes) FROM users WHERE users.u_id = $1) AND 1 < (SELECT count(users.u_id) FROM users WHERE pokes.id = any(users.pokes))",
                    user_id.id,
                    timeout=600,
                )
        result = "\n".join([str(x["id"]) for x in result])
        if not result:
            await ctx.send(f"No dupes for {user_id.id}!")
            return
        await ctx.send(f"Dupe list for {user_id.id}.\n```py\n{result[:1900]}```")

    @check_investigator()
    @commands.hybrid_command(aliases=("yeet", "bestow", "grant"))
    async def addpoke(self, ctx, userid: discord.Member, poke: int):
        """INVESTIGATOR: Add a pokemon by its ID to a user by their userID
        ex. ;addpoke <USERID> <POKEID>"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2",
                poke,
                userid.id,
            )
        await ctx.send("Successfully added the pokemon to the user specified.")

    @check_investigator()
    @commands.hybrid_command(aliases=("yoink", "rob", "take", "steal"))
    async def removepoke(self, ctx, userid: discord.Member, poke: int):
        """INVESTIGATOR: Remove a pokemon by its ID to a user by their userID
        ex. ;addpoke <USERID> <POKEID>"""
        try:
            await ctx.bot.commondb.remove_poke(userid.id, poke)
        except commondb.UserNotStartedError:
            await ctx.send("That user has not started!")
            return
        await ctx.send("Successfully removed the pokemon from users pokemon array")

    @check_helper()
    @commands.hybrid_command(aliases=["gi"])
    async def globalinfo(self, ctx, poke: int):
        """HELPER: Info a poke using its global id."""
        async with ctx.bot.db[0].acquire() as pconn:
            records = await pconn.fetchrow("SELECT * FROM pokes WHERE id = $1", poke)
        if records is None:
            await ctx.send("That pokemon does not exist.")
            return

        # An infotype is used here to prevent it from trying to associate this info with a person.
        # The function does not try to make it a market info unless it is explicitly market,
        # however it avoids user-specific info data if *any* value is passed.
        await ctx.send(embed=await get_pokemon_info(ctx, records, info_type="global"))

    @check_mod()
    @commands.hybrid_command()
    async def mock(self, ctx, user_id: discord.Member, *, raw):
        """MOD: 
        Mock another user invoking a command.
        
        The prefix must not be entered.
        """
        if not await self._mock_check(ctx.author.id, user_id.id):
            await ctx.send("Yeah, I'm not touching that.")
            return

        user = ctx.bot.get_user(user_id.id)
        if not user:
            try:
                user = await ctx.bot.fetch_user(user_id.id)
            except discord.HTTPException:
                await ctx.send("User not found.")
                return
        ctx.author = user
        class FakeInteraction():
            pass
        ctx._interaction = FakeInteraction()
        ctx._interaction.id = ctx.message.id

        path = []
        command = None
        args = ""
        # This is probably not super efficient, but I don't care to optimize
        # dev-facing code super hard...
        for part in raw.split(" "):
            if command is not None:
                args += part + " "
            else:
                path.append(part)
                if tuple(path) in ctx.bot.slash_commands:
                    command = ctx.bot.slash_commands[tuple(path)]
        if command is None:
            await ctx.send("I can't find a command that matches that input.")
            return
        # Just... trust me, this gets a list of type objects for the command's args
        signature = [x.annotation for x in inspect.signature(command.callback).parameters.values()][2:]
        view = StringView(args.strip())
        args = []
        for arg_type in signature:
            if view.eof:
                break
            arg = view.get_quoted_word()
            view.skip_ws()
            try:
                if arg_type in (str, inspect._empty):
                    pass
                elif arg_type in (discord.Member, discord.User):
                    arg = await MemberConverter().convert(ctx, arg)
                elif arg_type in (discord.TextChannel, discord.Channel):
                    arg = await TextChannelConverter().convert(ctx, arg)
                elif arg_type is int:
                    arg = int(arg)
                elif arg_type is bool:
                    arg = _convert_to_bool(arg)
                elif arg_type is float:
                    arg = float(arg)
                else:
                    await ctx.send(f"Unexpected parameter type, `{arg_type}`.")
                    return
            except Exception:
                await ctx.send("Could not convert an arg to the expected type.")
                return
            args.append(arg)
        try:
            com = command.callback(command.cog, ctx, *args)
        except TypeError:
            await ctx.send(
                "Too many args provided. Make sure you surround arguments that "
                "would have spaces in the slash UI with quotes."
            )
            return
        await com

    @check_mod()
    @commands.hybrid_command()
    async def mocksession(self, ctx, user_id: discord.Member):
        """MOD: Same as mock, but toggled on and off for total mocking of a user id"""
        if not await self._mock_check(ctx.author.id, user_id.id):
            await ctx.send("Yeah, I'm not touching that.")
            return

        user = ctx.bot.get_user(user_id.id)
        if not user:
            try:
                user = await ctx.bot.fetch_user(user_id.id)
            except discord.HTTPException:
                await ctx.send("User not found.")
                return

        if ctx.channel.id in self.sessions and ctx.author.id in self.sessions[ctx.channel.id]:
            await ctx.send("You are already running a mock session in this channel.")
            return
        elif ctx.channel.id in self.sessions:
            self.sessions[ctx.channel.id][ctx.author.id] = {}
        else:
            self.sessions[ctx.channel.id] = {}
            self.sessions[ctx.channel.id][ctx.author.id] = {}

        self.sessions[ctx.channel.id][ctx.author.id] = {"mocking": user, "last": time.time()}

        await ctx.send(
            "Mock session started.\nUse `:your_command_here` to run a command\nUse `m:Your message here` to fake a message\nUse `;mocksessionend` to stop."
        )

    @check_mod()
    @commands.hybrid_command()
    async def mocksessionend(self, ctx):
        """MOD: Ends the mocking session"""
        entry = None
        if ctx.channel.id not in self.sessions:
            await ctx.send("You are not running a mock session in this channel.")
            return

        if ctx.author.id not in self.sessions[ctx.channel.id]:
            await ctx.send("You are not running a mock session in this channel.")
            return

        del self.sessions[ctx.channel.id][ctx.author.id]
        if not self.sessions[ctx.channel.id]:
            del self.sessions[ctx.channel.id]
        await ctx.send("Mock session ended.")

    async def _mock_check(self, mocker: int, mocked: int):
        """Check if "mocker" has permission to mock "mocked"."""
        async with self.bot.db[0].acquire() as pconn:
            mocked_rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", mocked)
            if mocked_rank is None:
                return True
            mocked_rank = Rank[mocked_rank.upper()]
            mocker_rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", mocker)
            # Should not happen, but just in case
            if mocker_rank is None:
                return False
            mocker_rank = Rank[mocker_rank.upper()]
        return mocker_rank > mocked_rank

    @check_gymauth()
    @commands.hybrid_command()
    async def addev(self, ctx, userid: discord.Member, evs: int):
        """GYM: Add evs to a user by their ID"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET evpoints = evpoints + $1 WHERE u_id = $2",
                evs,
                userid.id,
            )
        await ctx.send("Successfully added Effort Value points to user")

    @check_admin()
    @commands.hybrid_command()
    async def marketyoink(self, ctx, market_id: int):
        """ADMIN: Remove a poke from the market, assigning it to user id 1227."""
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT poke, buyer FROM market WHERE id = $1", market_id
            )
            if not details:
                await ctx.send("That listing does not exist.")
                return
            poke, buyer = details
            if buyer is not None:
                await ctx.send("That listing has already ended.")
                return
            await pconn.execute("UPDATE market SET buyer = 0 WHERE id = $1", market_id)
            await pconn.execute(
                "UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = 1227", poke
            )
        await ctx.send(f"User `1227` now owns poke `{poke}`.")

    @check_mod()
    @commands.hybrid_command()
    async def marketmany(self, ctx, ids: str):
        """MOD: Buy multiple pokes from the market at once. Seperate ids by commas."""
        _ids = []

        for id in ids.replace(" ", ""):
            if id.isdigit():
                _ids.append(int(id))
        if not _ids:
            await ctx.send("No valid ids provided.")
            return
        
        ids = _ids

        c = ctx.bot.get_cog("Market")
        if c is None:
            await ctx.send("Market needs to be loaded to use this command!")
            return
        await ctx.send(
            f"Are you sure you want to buy {len(ids)} pokes?\n"
            f"Say `{ctx.prefix}confirm` to confirm or `{ctx.prefix}reject` to stop the market purchase."
        )

        def check(m):
            return (
                m.author == ctx.author
                and m.content.lower() in (f"{ctx.prefix}confirm", f"{ctx.prefix}reject")
                and m.channel == ctx.channel
            )

        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return
        if msg.content.lower() == f"{ctx.prefix}reject":
            await ctx.send("Market Purchase Canceled!")
            return
        locked = [
            int(id_)
            for id_ in await ctx.bot.redis_manager.redis.execute(
                "LRANGE", "marketlock", "0", "-1"
            )
            if id_.decode("utf-8").isdigit()
        ]
        funcs = [self._marketbuy(ctx, i, locked) for i in ids]
        results = await asyncio.gather(*funcs)
        types = [x[0] for x in results]
        msg = ""
        if types.count(None):
            msg += f"You successfully bought {types.count(None)} pokes.\n"
        if types.count("Locked"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "Locked"])
            msg += f"There is a marketlock on the following pokes: `{data}`\n"
        if types.count("InvalidID"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "InvalidID"])
            msg += f"The following market ids were invalid: `{data}`\n"
        if types.count("Owner"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "Owner"])
            msg += f"You already own the following listings: `{data}`\n"
        if types.count("Ended"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "Ended"])
            msg += f"The poke was already bought for the following listings: `{data}`\n"
        if types.count("InvalidPoke"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "InvalidPoke"])
            msg += (
                f"The pokemon from the listing was deleted for the following listings: `{data}`\n"
            )
        if types.count("LowBal"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "LowBal"])
            msg += f"You could not afford the following listings: `{data}`\n"
        if types.count("Error"):
            data = ", ".join([str(x[1]) for x in results if isinstance(x[0], Exception)])
            msg += f"An unknown error occurred in the following listings: `{data}`\n"
            data = [x[0] for x in results if isinstance(x[0], Exception)]
            msg += f"These are the exceptions: `{data}`\n"

        if not msg:
            msg = "No pokes were attempted to be bought?"
        await ctx.send(msg)

    @staticmethod
    async def _marketbuy(ctx, listing_id, locked):
        """Helper function to buy a poke from the market."""
        if listing_id in locked:
            return ("Locked", listing_id)
        await ctx.bot.redis_manager.redis.execute("LPUSH", "marketlock", str(listing_id))
        try:
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetchrow(
                    "SELECT poke, owner, price, buyer FROM market WHERE id = $1", listing_id
                )
                if not details:
                    return ("InvalidID", listing_id)
                poke, owner, price, buyer = details
                if owner == ctx.author.id:
                    return ("Owner", listing_id)
                if buyer is not None:
                    return ("Ended", listing_id)
                details = await pconn.fetchrow(
                    "SELECT pokname, pokelevel FROM pokes WHERE id = $1", poke
                )
                if not details:
                    return ("InvalidPoke", listing_id)
                pokename, pokelevel = details
                pokename = pokename.capitalize()
                credits = await pconn.fetchval(
                    "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
                )
                if price > credits:
                    return ("LowBal", listing_id)
                await pconn.execute(
                    "UPDATE market SET buyer = $1 WHERE id = $2", ctx.author.id, listing_id
                )
                await pconn.execute(
                    "UPDATE users SET pokes = array_append(pokes, $1), mewcoins = mewcoins - $2 WHERE u_id = $3",
                    poke,
                    price,
                    ctx.author.id,
                )
                gain = price
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                    gain,
                    owner,
                )
                try:
                    user = await ctx.bot.fetch_user(owner)
                    await user.send(
                        f"<@{owner}> Your {pokename} has been sold for {price} credits."
                    )
                except discord.HTTPException:
                    pass
                await ctx.bot.log(
                    557926149284691969,
                    f"{ctx.author.name} - {ctx.author.id} has bought a {pokename} on the market. Seller - {owner}. Listing id - {listing_id}",
                )
        except Exception as e:
            return (e, listing_id)
        finally:
            await ctx.bot.redis_manager.redis.execute(
                "LREM", "marketlock", "1", str(listing_id)
            )
        return (None, None)

    @check_admin()
    @commands.hybrid_command()
    async def grantsupport(self, ctx, member: discord.Member):
        """MOD: Promote a user to Support Team"""
        com = ctx.bot.get_command("promote staff")
        if com is None:
            await ctx.send("The `promote staff` command needs to be loaded to use this!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            rank = await pconn.fetchval("SELECT staff FROM users WHERE u_id = $1", member.id)
        if rank != "User":
            await ctx.send("You cannot grant support to that user.")
            return
        await com.callback(com.cog, ctx, "support", member)


    @check_gymauth()
    @commands.hybrid_command()
    async def gym_reward(self, ctx, mewcoins: int, user: int):
        """GYM-AUTH: Gym mewcoins Reward"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                mewcoins,
                user,
            )
        #if ctx.author.id not in (790722073248661525,473541068378341376,709695571379617863,728736503366156361):
        #   await ctx.send("...no.")
        #    return
        username = ctx.message.author.name
        #message = EmailMessage()
        #message["From"] = "admin@skys.fun"
        #message["To"] = "skylarr12227@gmail.com"
        #message["Subject"] = f"{username} gave {user}, {mewcoins} mewcoins in gym server"
        #message.set_content(f"{username} gave {user}, {mewcoins} mewcoins in gym server")
        #await aiosmtplib.send(message, hostname="a2plcpnl0218.prod.iad2.secureserver.net", port=465, username="admin@skys.fun", password="liger666", use_tls=True)
        api_url = 'https://hooks.zapier.com/hooks/catch/6433731/bykhq8m/'
        json_data = {'gym_reward': mewcoins, 'u_id': str(user), 'username': str(username)}
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=json_data) as r:
                pass
        await ctx.bot.http.send_message(882419606134874192, f"{ctx.author}: <@{user}> has been awarded {mewcoins} for a gym challenge.")
        await ctx.send(f"<@{user}> has been awarded {mewcoins} for a gym challenge.\n")

    
    
    @check_investigator()
    @commands.hybrid_command(aliases=["serverban"])
    async def banserver(self, ctx, id: int):
        """INVESTIGATOR: Ban a server"""
        sbans = set(ctx.bot.banned_guilds)
        if id in sbans:
            await ctx.send("That server is already banned.")
            return
        sbans.add(id)
        await ctx.bot.mongo_update("blacklist", {}, {"guilds": list(sbans)})
        await ctx.send(f"```Elm\n-Successfully Banned {await ctx.bot.fetch_guild(id)}```")
        await self.load_bans_cross_cluster()

    @check_investigator()
    @commands.hybrid_command(aliases=["serverunban", "unserverban"])
    async def unbanserver(self, ctx, id: int):
        """INVESTIGATOR: UNBan a server"""
        sbans = set(ctx.bot.banned_guilds)
        if id not in sbans:
            await ctx.send("That server is not banned.")
            return
        sbans.remove(id)
        await ctx.bot.mongo_update("blacklist", {}, {"guilds": list(sbans)})
        await ctx.send(f"```Elm\n- Successfully Unbanned {await ctx.bot.fetch_guild(id)}```")
        await self.load_bans_cross_cluster()

    @check_gymauth()
    @commands.hybrid_command(aliases=["duelban"])
    async def duelblock(self, ctx, id: int):
        """GYM-AUTH: Ban a user from duels"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE botbans SET duelban = array_append(duelban, $1)", id)
            await ctx.send(f"```Elm\n- Successflly Duelbanned {await ctx.bot.fetch_user(id)}```")

    @check_gymauth()
    @commands.hybrid_command(aliases=["duelunban", "unduelban"])
    async def unduelblock(self, ctx, id: int):
        """GYM-AUTH: UNBan a user from duels"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE botbans SET duelban = array_remove(duelban, $1)", id)
            await ctx.send(
                f"```Elm\n- Successfully unduelbanned {await ctx.bot.fetch_user(id)}```"
            )

    # @check_helper()
    # @commands.hybrid_command()
    # async def textsky(self, ctx, text: str):
    #     """HELPER: Send a text to sky"""
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post('https://textbelt.com/text', json={
    #             'phone': '5029746666',
    #             'message': text,
    #             'replyWebhookUrl': 'https://hooks.zapier.com/hooks/catch/6433731/by0jj91/',
    #             'key': 'a7684210ed572847d8854fc05c9e8e9a49b062c4pVb5Xb1BxIjBI1W71pzu7kVgP', }) as r:
    #             embed = discord.Embed(title="Successfully sent!", description=f"Message sent to Sky's phone.")
    #             embed.set_footer(text="better be important...")
    #             if str(r.status)[0] == "2":
    #                 return await ctx.send(embed=embed)
    #             else:
    #                 return await ctx.send("Failed to send")

    @check_admin()
    @commands.hybrid_command()
    async def combine(self, ctx, u_id1: int, u_id2: int):
        """ADMIN: Add two users pokes together, leaving user1 with all, and user2 with none."""
        await ctx.send(f"Are you sure you want to move all pokemon from {u_id2} to {u_id1}?")
        def check(m):
            return m.author.id == ctx.author.id and m.content.lower() in (
                "yes",
                "no",
                "y",
                "n",
            )
        try:
            m = await ctx.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("Request timed out.")
            return
        if m.content.lower().startswith("n"):
            await ctx.send("Cancelled.")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            user1 = await pconn.fetchval(
                "SELECT pokes FROM users WHERE u_id = $1", u_id1
            )
            user2 = await pconn.fetchval(
                "SELECT pokes FROM users WHERE u_id = $1", u_id2
            )
            user1.extend(user2)
            user2 = []
            await pconn.execute(
                "UPDATE users SET pokes = $2 WHERE u_id = $1", u_id1, user1
            )
            await pconn.execute(
                "UPDATE users SET pokes = $2 WHERE u_id = $1", u_id2, user2
            )
        await ctx.send(f"```elm\nSuccessfully added pokemon from {u_id2} to {u_id1}.```")

#    
#    @check_mod()
#    @commands.hybrid_command()
#    async def rchest(self, ctx, uid: int, chest, num: int):
#        """CHEESE-ONLY: Add a chest"""
#        if ctx.author.id not in (790722073248661525,478605505145864193):
#            await ctx.send("...no.")
#            return
#        elif chest == "legend":
#            actualchest = "legend chest"
#        elif chest == "mythic":
#            actualchest = "mythic chest"
#        elif chest == "rare":
#            actualchest = "rare chest"
#        elif chest == "common":
#            actualchest = "common chest"
#        async with ctx.bot.db[0].acquire() as pconn:
#            inventory = await pconn.fetchval(
#                "SELECT inventory::json FROM users WHERE u_id = $1", uid 
#            )
#            inventory[actualchest ] = inventory.get(actualchest , 0) + num
#            await pconn.execute(
#                "UPDATE users SET inventory = $1::json where u_id = $2",
#                inventory,
#                uid ,
#            )
#            await ctx.send(f"<@{uid}> gained `{num}` `{actualchest}'s`")

    @check_mod()
    @commands.hybrid_command(aliases=["ot"])
    async def findot(self, ctx, poke: int):
        """HELPER: Find the OT userid of a pokemon"""
        async with ctx.bot.db[0].acquire() as pconn:
            caught_by = await pconn.fetchval("SELECT caught_by FROM pokes WHERE id = $1", poke)
        if caught_by is None:
            await ctx.send("That pokemon does not exist.")
            return
        await ctx.send(f"`{caught_by}`")

    @check_admin()
    @commands.hybrid_command(aliases=["fr"])
    async def forcerelease(self, ctx, user: discord.Member, pokemon_number: str = None):
        """ADMIN: Force release a pokemon from  a user"""
        if not pokemon_number is None:
            if pokemon_number.lower() == "latest":
                async with ctx.bot.db[0].acquire() as pconn:
                    pokes = await pconn.fetchval(
                        "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1",
                        user.id,
                    )
                pokes = pokes.split()
            else:
                pokes = pokemon_number.split()
            try:
                pokes = [int(x) for x in pokes]
            except:
                await ctx.send("Invalid Pokemon Number(s)")
                return
            ids = []
            async with ctx.bot.db[0].acquire() as pconn:
                stmt = await pconn.prepare("SELECT pokes[$1] FROM users WHERE u_id = $2")
                for poke in pokes:
                    id = await stmt.fetchval(poke, user.id)
                    if id == None:
                        await ctx.send("You do not have that Pokemon!")
                        return
                    else:
                        ids.append(id)
                query = f"SELECT pokname FROM pokes WHERE id {'=' if len(ids) == 1 else 'in'} {ids[0] if len(ids) == 1 else tuple(ids)}"
                pokenames = await pconn.fetch(query)
            pokenames = [t["pokname"] for t in pokenames]
            await ctx.send(
                f"You are releasing {', '.join(pokenames).capitalize()}\nSay `"
                + await pre(ctx.bot, ctx.message)
                + "confirm` or `"
                + await pre(ctx.bot, ctx.message)
                + "reject`"
            )
            prefix = await pre(ctx.bot, ctx.message)

            def check(m):
                return m.author.id == ctx.author.id and m.content in (
                    f"{prefix}confirm",
                    f"{prefix}reject",
                )

            try:
                msg = await ctx.bot.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("Release cancelled, took too long to confirm")
                return
            if msg.content.lower() == f"{await pre(ctx.bot, ctx.message)}reject":
                await ctx.send("Release cancelled")
                return
            elif msg.content.lower() == f"{await pre(ctx.bot, ctx.message)}confirm":
                async with ctx.bot.db[0].acquire() as pconn:
                    for poke_id in ids:
                        await pconn.execute(
                            "UPDATE users SET pokes = array_remove(pokes, $1) WHERE u_id = $2",
                            poke_id,
                            user.id,
                        )
            await ctx.send(
                f"You have successfully released {', '.join(pokenames).capitalize()} from {user.name}"
            )

        else:
            await ctx.send("You dont have that Pokemon")

    @check_admin()
    @commands.hybrid_command()
    async def announce(self, ctx, *, announce_msg):
        """ADMIN: FUTURE USE"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO announce (announce, staff) VALUES ($1, $2)",
                announce_msg,
                ctx.author.mention,
            )
        await ctx.send("Bot announcement has been Added")

    @check_admin()
    @commands.hybrid_command()
    async def setot(self, ctx, id: int, userid: discord.Member):
        """ADMIN: Set pokes OT"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE pokes SET caught_by = $1 where id = $2", userid.id, id)
            await ctx.send(f"```Elm\n- Successflly set OT of `{id}` to {await ctx.bot.fetch_user(userid.id)}```")

    

    @check_mod()
    @commands.hybrid_command()
    async def getuser(self, ctx, user: int):
        """MOD: Get user info by ID"""
        async with ctx.bot.db[0].acquire() as pconn:
            info = await pconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", user
            )
        if info is None:
            await ctx.send("User has not started.")
            return
        pokes = info["pokes"]
        count = len(pokes)
        uid = info["id"]
        redeems = info["redeems"]
        evpoints = info["evpoints"]
        tnick = info["tnick"]
        upvote = info["upvotepoints"]
        mewcoins = info["mewcoins"]
        inv = info["inventory"]
        daycare = info["daycare"]
        dlimit = info["daycarelimit"]
        energy = info["energy"]
        fishing_exp = info["fishing_exp"]
        fishing_level = info["fishing_level"]
        party = info["party"]
        luck = info["luck"]
        selected = info["selected"]
        visible = info["visible"]
        voted = info["voted"]
        tradelock = info["tradelock"]
        botbanned = ctx.bot.botbanned(user)
        mlimit = info["marketlimit"]
        staff = info["staff"]
        gym_leader = info["gym_leader"]
        patreon_tier = await ctx.bot.patreon_tier(user)
        intrade = user in [
            int(id_)
            for id_ in await ctx.bot.redis_manager.redis.execute(
                "LRANGE", "tradelock", "0", "-1"
            )
            if id_.decode("utf-8").isdigit()
        ]
        desc =  f"**__Information on {user}__**"
        desc += f"\n**Trainer Nickname**: `{tnick}`"
        desc += f"\n**MewbotID**: `{uid}`"
        desc += f"\n**Patreon Tier**: `{patreon_tier}`"
        desc += f"\n**Staff Rank**: `{staff}`"
        desc += f"\n**Gym Leader?**: `{gym_leader}`"
        desc += f"\n**Selected Party**: `{party}`"
        desc += f"\n**Selected Pokemon**: `{selected}`"
        desc += f"\n**Pokemon Owned**: `{count}`"
        desc += f"\n**Mewcoins**: `{mewcoins}`"
        desc += f"\n**Redeems**: `{redeems}`"
        desc += f"\n**EvPoints**: `{evpoints}`"
        desc += f"\n**UpVOTE Points**: `{upvote}`"
        desc += f"\n\n**Daycare Slots**: `{daycare}`"
        desc += f"\n**Daycare Limit**: `{dlimit}`"
        desc += f"\n**Market Limit**: `{mlimit}`"
        desc += f"\n\n**Energy**: `{energy}`"
        desc += f"\n**Fishing Exp**: `{fishing_exp}`"
        desc += f"\n**Fishing Level**: `{fishing_level}`"
        desc += f"\n**Luck**: `{luck}`"
        desc += f"\n\n**Visible Balance?**: `{visible}`"
        desc += f"\n**Voted?**: `{voted}`"
        desc += f"\n**Tradebanned?**: `{tradelock}`"
        desc += f"\n**In a trade?**: `{intrade}`"
        desc += f"\n**Botbanned?**: `{botbanned}`"
        embed = discord.Embed(color=0xFFB6C1, description=desc)
        embed.add_field(name=f"Inventory", value=f"{inv}", inline=False)
        embed.set_footer(text="Information live from Database")
        await ctx.send(embed=embed)

    @check_helper()
    @commands.hybrid_command()
    async def getpoke(self, ctx, pokem: int):
        """MOD: Get pokemon info by ID"""
        async with ctx.bot.db[0].acquire() as pconn:
            info = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = $1", pokem
            )
            info2 = await pconn.fetchval(
                "SELECT age(time_stamp) FROM pokes WHERE id = $1", pokem
            )
            tradeinfo = await pconn.fetch(
                "SELECT * FROM trade_logs WHERE $1 = any(sender_pokes) OR $1 = any(receiver_pokes) order by t_id DESC limit 4", pokem
            )
            tradeage = await pconn.fetch(
                "SELECT age(time) FROM trade_logs WHERE $1 = any(sender_pokes) OR $1 = any(receiver_pokes) order by t_id DESC limit 4", pokem
            )
        if info is None:
            await ctx.send("Global ID not valid.")
            return
        id = info["id"]
        pokname = info["pokname"]
        hpiv = info["hpiv"]
        atkiv = info["atkiv"]
        defiv = info["defiv"]
        spatkiv = info["spatkiv"]
        spdefiv = info["spdefiv"]
        speediv = info["speediv"]
        hpev = info["hpev"]
        atkev = info["atkev"]
        defev = info["defev"]
        spatkev = info["spatkev"]
        spdefev = info["spdefev"]
        speedev = info["speedev"]
        pokelevel = info["pokelevel"]
        moves = info["moves"]
        hitem = info["hitem"]
        nature = info["nature"]
        poknick = info["poknick"]
        happiness = info["happiness"]
        ability_index = ["ability_index"]
        gender = info["gender"]
        shiny = info["shiny"]
        counter = info["counter"]
        name = info["name"]
        caught_at = info2.days
        caught_by = info["caught_by"]
        radiant = info["radiant"]
        
        def age_get(age):
            trade_age = math.ceil(abs(age.total_seconds()))
            trade_age_min, trade_age_sec = divmod(trade_age, 60)
            trade_age_hr, trade_age_min = divmod(trade_age_min, 60)
            return trade_age_hr, trade_age_min, trade_age_sec

        desc =  f"**__Information on pokemon:`{pokem}`__**"
        desc += f"\n**Name**: `{pokname}` "
        desc += f"| **Nickname**: `{poknick}`"
        desc += f"| **Level**: `{pokelevel}`"
        desc += f"\n**IV's**: `{hpiv}|{atkiv}|{defiv}|{spatkiv}|{spdefiv}|{speediv}` "
        desc += f"| **EV's**: `{hpev}|{atkev}|{defev}|{spatkev}|{spdefev}|{speedev}`"
        desc += f"\n**Held Item**: `{hitem}` "
        desc += f"\n| **Happiness**: `{happiness}` "
        #desc += f"|**Ability ID**: `{ability_index}`"
        desc += f"| **Gender**: `{gender}`"
        desc += f"\n**Is Shiny**: `{shiny}` "
        desc += f"| **Is Radiant**: `{radiant}`"
        desc += f"\n**Age**: `{caught_at}` days "
        desc += f"\n**O.T.**: `{caught_by}`"
        if pokname.lower() == "egg":
            desc += f"Egg-Remaining Steps: `{counter}`"
        embed = discord.Embed(color=0xFFB6C1, description=desc)
        embed.add_field(name=f"Moves", value=", ".join(moves), inline=False)
        if not tradeinfo:
            embed.add_field(name=f"Trade History", value=f"```No trade info found```", inline=False)
        else:
            embed.add_field(name=f".", value=f"<:image_part_0011:871809643054243891><:image_part_0021:871809642928406618><:image_part_0021:871809642928406618><:image_part_0021:871809642928406618><:image_part_0021:871809642928406618><:image_part_003:871809643020693504>", inline=False)
            i = 1
            for trade in tradeinfo:
                try:
                    hr, minu, sec = age_get(tradeage[i-1]["age"])
                except Exception as exc:
                    hr, minu, sec = "Unknown", "Unknown", str(exc)
                embed.add_field(name=f"Trade #{i}", value=f"**Sender**: `{trade['sender']}`\n**Receiver**: `{trade['receiver']}`\n**Trade Command:** `{trade['command']}`\n**Traded:** `{hr} hours, {minu} minutes and {sec} seconds`", inline=False)
                i+=1
                
        embed.set_footer(text="Information live from Database")
        await ctx.send(embed=embed)

    @check_admin()
    @commands.hybrid_command()
    async def set_skin(self, ctx, pokeid: int, skinid):
        """ADMIN: Add a skin to users pokemon"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET skin = $1 WHERE id = $2",
                skinid,
                pokeid,
            )
        await ctx.send("Successfully added skin to pokemon")
    
    @check_admin()
    @commands.hybrid_command()
    async def give_skin(self, ctx, userid: discord.Member, pokname: str, skinname: str):
        """ADMIN: Give a skin to a user"""
        pokname = pokname.lower()
        skinname = skinname.lower()
        async with ctx.bot.db[0].acquire() as pconn:
            skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", userid.id)
            if pokname not in skins:
                skins[pokname] = {}
            if skinname not in skins[pokname]:
                skins[pokname][skinname] = 1
            else:
                skins[pokname][skinname] += 1
            await pconn.execute("UPDATE users SET skins = $1::json WHERE u_id = $2", skins, userid.id)
        await ctx.send(f"Gave `{userid.name}({userid.id})` a `{skinname}` skin for `{pokname}`.")

    @check_admin()
    @commands.hybrid_command()
    async def make_first(self, ctx, user: int, poke_id: int):
        """ADMIN: Change a users poke to their #1 spot"""
        async with ctx.bot.db[0].acquire() as pconn: 
            poke_id = await pconn.fetchval('SELECT pokes[$1] FROM users WHERE u_id = $2', poke_id, user)
            if poke_id is None:
                await ctx.send("That user does not have that many pokes, or does not exist!")
                return
            await pconn.execute('UPDATE users SET pokes = array_remove(pokes, $1) WHERE u_id = $2', poke_id, user)
            await pconn.execute('UPDATE users SET pokes = array_prepend($1, pokes) WHERE u_id = $2', poke_id, user)
        await ctx.send("Successfully changed poke to users #1")
    
    @check_investigator()
    @commands.group(aliases=["tradelogs", "tl"])
    async def tradelog(self, ctx):
        """INVESTIGATOR: Tradelog command"""
        pass
    
    @tradelog.command(name="user")
    async def tradelog_user(self, ctx, u_id: int):
        async with ctx.bot.db[0].acquire() as pconn:
            trade_sender = await pconn.fetch("SELECT * FROM trade_logs WHERE $1 = sender ORDER BY t_id ASC", u_id)
            trade_receiver = await pconn.fetch("SELECT * FROM trade_logs WHERE $1 = receiver ORDER BY t_id ASC", u_id)
        # List[Tuple] -> (T_ID, Optional[DateTime], Traded With, Sent Creds, Sent Redeems, # Sent Pokes, Rec Creds, Rec Redeems, # Rec Pokes)
        trade = []
        t_s = trade_sender.pop(0) if trade_sender else None
        t_r = trade_receiver.pop(0) if trade_receiver else None
        while t_s or t_r:
            if t_s is None:
                trade.append((
                    t_r["t_id"], t_r["time"], t_r["sender"],
                    t_r["receiver_credits"], t_r["receiver_redeems"], len(t_r["receiver_pokes"]),
                    t_r["sender_credits"], t_r["sender_redeems"], len(t_r["sender_pokes"])
                ))
                t_r = trade_receiver.pop(0) if trade_receiver else None
            elif t_r is None:
                trade.append((
                    t_s["t_id"], t_s["time"], t_s["receiver"],
                    t_s["sender_credits"], t_s["sender_redeems"], len(t_s["sender_pokes"]),
                    t_s["receiver_credits"], t_s["receiver_redeems"], len(t_s["receiver_pokes"])
                ))
                t_s = trade_sender.pop(0) if trade_sender else None
            elif t_s["t_id"] > t_r["t_id"]:
                trade.append((
                    t_r["t_id"], t_r["time"], t_r["sender"],
                    t_r["receiver_credits"], t_r["receiver_redeems"], len(t_r["receiver_pokes"]),
                    t_r["sender_credits"], t_r["sender_redeems"], len(t_r["sender_pokes"])
                ))
                t_r = trade_receiver.pop(0) if trade_receiver else None
            else:
                trade.append((
                    t_s["t_id"], t_s["time"], t_s["receiver"],
                    t_s["sender_credits"], t_s["sender_redeems"], len(t_s["sender_pokes"]),
                    t_s["receiver_credits"], t_s["receiver_redeems"], len(t_s["receiver_pokes"])
                ))
                t_s = trade_sender.pop(0) if trade_sender else None
        
        if not trade:
            await ctx.send("That user has not traded!")
            return
        
        raw = ""
        now = datetime.datetime.now(datetime.timezone.utc)
        name_map = {}
        for t in trade:
            if t[1] is None:
                time = '?'
            else:
                d = t[1]
                d = now - d
                if d.days:
                    time = str(d.days) + 'd'
                elif d.seconds // 3600:
                    time = str(d.seconds // 3600) + 'h'
                elif d.seconds // 60:
                    time = str(d.seconds // 60) + 'm'
                elif d.seconds:
                    time = str(d.seconds) + 's'
                else:
                    time = '?'
            if t[2] in name_map:
                un = name_map[t[2]]
            else:
                try:
                    un = f"{await ctx.bot.fetch_user(int(t[2]))} ({t[2]})"
                except discord.HTTPException:
                    un = t[2]
                name_map[t[2]] = un
            raw += f"__**{t[0]}** - {un}__ ({time} ago)\n"
            raw += f"Gave: {t[3]} creds + {t[4]} redeems + {t[5]} pokes\n"
            raw += f"Got: {t[6]} creds + {t[7]} redeems + {t[8]} pokes\n\n"
        
        PER_PAGE = 15
        page = ""
        pages = []
        raw = raw.strip().split("\n\n")
        total_pages = ((len(raw) - 1) // PER_PAGE) + 1
        for idx, part in enumerate(raw):
            page += part + "\n\n"
            if idx % PER_PAGE == PER_PAGE - 1 or idx == len(raw) - 1:
                embed = discord.Embed(title=f"Trade history of user {u_id}", description=page, color=0xDD00DD)
                embed.set_footer(text=f"Page {(idx // PER_PAGE) + 1}/{total_pages}")
                pages.append(embed)
                page = ""

        await MenuView(ctx, pages).start()

    @tradelog.command(name="poke")
    async def tradelog_poke(self, ctx, p_id: int):
        async with ctx.bot.db[0].acquire() as pconn:
            trade_sender = await pconn.fetch("SELECT * FROM trade_logs WHERE $1 = any(sender_pokes) ORDER BY t_id ASC", p_id)
            trade_receiver = await pconn.fetch("SELECT * FROM trade_logs WHERE $1 = any(receiver_pokes) ORDER BY t_id ASC", p_id)
        # List[Tuple] -> (T_ID, Optional[DateTime], Sender, Receiver)
        trade = []
        t_s = trade_sender.pop(0) if trade_sender else None
        t_r = trade_receiver.pop(0) if trade_receiver else None
        while t_s or t_r:
            if t_s is None:
                trade.append((t_r["t_id"], t_r["time"], t_r["receiver"], t_r["sender"]))
                t_r = trade_receiver.pop(0) if trade_receiver else None
            elif t_r is None:
                trade.append((t_s["t_id"], t_s["time"], t_s["sender"], t_s["receiver"]))
                t_s = trade_sender.pop(0) if trade_sender else None
            elif t_s["t_id"] > t_r["t_id"]:
                trade.append((t_r["t_id"], t_r["time"], t_r["receiver"], t_r["sender"]))
                t_r = trade_receiver.pop(0) if trade_receiver else None
            else:
                trade.append((t_s["t_id"], t_s["time"], t_s["sender"], t_s["receiver"]))
                t_s = trade_sender.pop(0) if trade_sender else None
        
        if not trade:
            await ctx.send("That pokemon has not been traded!")
            return
        
        raw = ""
        now = datetime.datetime.now(datetime.timezone.utc)
        for t in trade:
            if t[1] is None:
                time = '?'
            else:
                d = t[1]
                d = now - d
                if d.days:
                    time = str(d.days) + 'd'
                elif d.seconds // 3600:
                    time = str(d.seconds // 3600) + 'h'
                elif d.seconds // 60:
                    time = str(d.seconds // 60) + 'm'
                elif d.seconds:
                    time = str(d.seconds) + 's'
                else:
                    time = '?'
            raw += f"**{t[0]}**: {t[2]} -> {t[3]} ({time} ago)\n"

        PER_PAGE = 15
        page = ""
        pages = []
        raw = raw.strip().split("\n")
        total_pages = ((len(raw) - 1) // PER_PAGE) + 1
        for idx, part in enumerate(raw):
            page += part + "\n"
            if idx % PER_PAGE == PER_PAGE - 1 or idx == len(raw) - 1:
                embed = discord.Embed(title=f"Trade history of poke {p_id}", description=page, color=0xDD00DD)
                embed.set_footer(text=f"Page {(idx // PER_PAGE) + 1}/{total_pages}")
                pages.append(embed)
                page = ""

        await MenuView(ctx, pages).start()

    @tradelog.command(name="info")
    async def tradelog_info(self, ctx, t_id: int):
        """Get information on a specific trade by transaction id."""
        async with ctx.bot.db[0].acquire() as pconn:
            trade = await pconn.fetchrow("SELECT * FROM trade_logs WHERE t_id = $1", t_id)
        if trade is None:
            await ctx.send("That transaction id does not exist!")
            return
        desc = ""
        if trade["sender_credits"] or trade["sender_pokes"] or trade["sender_redeems"]:
            desc += f"**{trade['receiver']} received:**\n"
            if trade["sender_credits"]:
                desc += f"__Credits:__ {trade['sender_credits']}\n"
            if trade["sender_redeems"]:
                desc += f"__Redeems:__ {trade['sender_redeems']}\n"
            if trade["sender_pokes"]:
                desc += f"__Pokes:__ {trade['sender_pokes']}\n"
            desc += "\n"
        if trade["receiver_credits"] or trade["receiver_pokes"] or trade["receiver_redeems"]:
            desc += f"**{trade['sender']} received:**\n"
            if trade["receiver_credits"]:
                desc += f"__Credits:__ {trade['receiver_credits']}\n"
            if trade["receiver_redeems"]:
                desc += f"__Redeems:__ {trade['receiver_redeems']}\n"
            if trade["receiver_pokes"]:
                desc += f"__Pokes:__ {trade['receiver_pokes']}\n"
        embed = discord.Embed(title=f"Trade ID {t_id}", description=desc, color=0xDD00DD)
        if trade["time"] is not None:
            embed.set_footer(text=trade["time"].isoformat(" "))
        await ctx.send(embed=embed)

    @check_admin()
    @commands.hybrid_command(aliases=["skydb"])
    async def unsafeedb(self, ctx, type, *, execution: str):
        """DEV: No timeout EDB """
        await ctx.send("...no.")
        return
        
        # Sanity checks
        low_exe = execution.lower()
        if low_exe != self.safe_edb:
            self.safe_edb = low_exe
            if "update" in low_exe and "where" not in low_exe:
                await ctx.send("**WARNING**: You attempted to run an `UPDATE` without a `WHERE` clause. If you are **absolutely sure** this action is safe, run this command again.")
                return
            if "drop" in low_exe:
                await ctx.send("**WARNING**: You attempted to run a `DROP`. If you are **absolutely sure** this action is safe, run this command again.")
                return
            if "delete from" in low_exe:
                await ctx.send("**WARNING**: You attempted to run a `DELETE FROM`. If you are **absolutely sure** this action is safe, run this command again.")
                return
        
        try:
            async with ctx.bot.db[0].acquire() as pconn:
                if type == "row":
                    result = await pconn.fetchrow(execution, timeout=100)
                elif type == "fetch":
                    result = await pconn.fetch(execution, timeout=100)
                elif type == "val":
                    result = await pconn.fetchval(execution, timeout=100)
                elif type == "execute":
                    result = await pconn.execute(execution, timeout=100)
        except Exception as e:
            await ctx.send(f"```py\n{e}```")
            raise
        result = str(result)
        if len(result) > 1950:
            result = result[:1950] + "\n\n..."
        await ctx.send(f"```py\n{result}```")

    @check_admin()
    @commands.hybrid_command(aliases=["raffle"])
    async def raffle_winner(self, ctx):
        """ADMIN: Raffle command"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch("SELECT raffle, u_id FROM users WHERE raffle > 0")
        uids = []
        weights = []
        for user in data:
            uids.append(user["u_id"])
            weights.append(user["raffle"])
        winnerid = random.choices(uids, weights=weights)[0]
        winner = await ctx.bot.fetch_user(winnerid)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET raffle = raffle - 1 WHERE u_id = $1",
                winnerid,
            )
        await ctx.send("<:3_:924118114671665243>")
        await asyncio.sleep(1)
        await ctx.send("<:2:924118115103674418>")
        await asyncio.sleep(1)
        await ctx.send("<:1:924118115078524928>")
        await asyncio.sleep(1)
        await ctx.send(f"Winner - **{winner}** ({winnerid})")

    @commands.hybrid_command(aliases=["pride_skins"])
    async def view_skins_pride(self, ctx):
        """PUBLIC: View Pride 2022 Skins"""
        pages = []
        SERVER_BASE_PRIDE_SKIN = "https://dyleee.github.io/mewbot-images/sprites/skins/pride2022/"
        PRIDE_BASE = "/home/dylee/clustered/shared/duel/sprites/skins/pride2022/"
        pages = []
        skins = list(pathlib.Path(PRIDE_BASE).glob("*-*-.png"))
        total = len(skins)
        for idx, path in enumerate(skins, 1):
            pokeid = int(path.name.split("-")[0])
            pokename = (await ctx.bot.db[1].forms.find_one({"pokemon_id": pokeid}))["identifier"]
            embed = discord.Embed(
                title=f"{pokename} - PRIDE EVENT 2022 ",
                color=0xDD22DD,
            )
            embed.set_image(url=SERVER_BASE_PRIDE_SKIN + path.name)
            embed.set_footer(text=f"Page {idx}/{total}")
            pages.append(embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_command(aliases=["skins"])
    async def view_skins(self, ctx, *, skin_name=None):
        """PUBLIC: View ALL Skins (not functional currently)"""
        pages = []
        skins = list(pathlib.Path(SKIN_BASE).glob("*-*-.png"))
        if skin_name is not None:
            skins = [x for x in skins if x.name.split("_")[1][:-4] == skin_name]
        total = len(skins)
        for idx, path in enumerate(skins, 1):
            #skin = path.name.split("_")[1][:-4]
            pokeid = int(path.name.split("-")[0])
            pokename = (await ctx.bot.db[1].forms.find_one({"pokemon_id": pokeid}))["identifier"]
            embed = discord.Embed(
                title=f"{pokename} - {skin}",
                color=0xDD22DD,
            )
            embed.set_image(url=IMG_SERVER_BASE_SKIN + path.name)
            embed.set_footer(text=f"Page {idx}/{total}")
            pages.append(embed)
        await MenuView(ctx, pages).start()
    
    @commands.hybrid_command(aliases=["radiants"])
    async def view_rads(self, ctx):
        """PUBLIC: View All released radiants"""
        pages = []
        skins = list(pathlib.Path(RAD_BASE).glob("*-*-.png"))
        total = len(skins)
        for idx, path in enumerate(skins, 1):
            pokeid = int(path.name.split("-")[0])
            pokename = (await ctx.bot.db[1].forms.find_one({"pokemon_id": pokeid}))["identifier"]
            embed = discord.Embed(
                title=f"{pokename}",
                color=0xDD22DD,
            )
            embed.set_image(url=IMG_SERVER_BASE_RAD + path.name)
            embed.set_footer(text=f"Page {idx}/{total}")
            pages.append(embed)
        await MenuView(ctx, pages).start()

    @check_mod()
    @commands.hybrid_command()
    async def gib_support(self, ctx, redeems: int):
        """CHICHIRI: Add redeems to all support team"""
        await ctx.send("get out of here....no.")
        return
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $1 WHERE staff = 'Support'",
                redeems,
            )
            await ctx.send(f"Support team rewarded with {redeems} redeems. Thank you for all that you guys do!<3")

    @check_helper()
    @commands.hybrid_command()
    async def credits_donated(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetchval("select mewcoins from users where u_id = 920827966928326686")
            embed = discord.Embed(title="**Total Credits Donated**", description=f"```{data}```")
            embed.set_footer(text="Raffle is on Christmas!")
            await ctx.send(embed=embed)
       
    @check_mod()  
    @commands.hybrid_command()
    async def irefresh(self, ctx):
        """MOD: IMAGE REFRESH, pull new images to both servers"""
        COMMAND = "rsync -avz --delete /var/www/mewbot.xyz/html/sprites/ /home/dylee/clustered/shared/duel/sprites/"
        proc = await asyncio.create_subprocess_shell(COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        stdout = stdout.decode()

        if "sent" not in stdout:
            await ctx.send("Image Syncing Failed.")
            ctx.bot.logger.warning(stdout)
            return
        
        await ctx.send("Images Synced Successfully.")

        # COMMAND = f"sshpass -p liger666 ssh -A root@images.mewbot.xyz \"cd /var/www/html/img/sprites/ && git pull\" && cd /home/dylee/clustered/shared/duel/sprites/ && git pull"
        # addendum = ""

        # proc = await asyncio.create_subprocess_shell(COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        # stdout, stderr = await proc.communicate()
        # stdout = stdout.decode()

        # if "no tracking information" in stderr.decode():
        #     COMMAND = f"sshpass -p liger666 ssh -A root@images.mewbot.xyz \"cd /var/www/html/img/sprites/ && git pull\" && cd /home/dylee/clustered/shared/duel/sprites/ && git pull"
        #     proc = await asyncio.create_subprocess_shell(COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        #     stdout, stderr = await proc.communicate()
        #     stdout = stdout.decode()
        #     addendum = "\n\n**Warning: no upstream branch is set.  I automatically pulled from origin/clustered but this may be wrong.  To remove this message and make it dynamic, please run `git branch --set-upstream-to=origin/<branch> <branch>`**"

        # embed = discord.Embed(title="Image Refresh", description="", color=0xFFB6C1)

        # if "Fast-forward" not in stdout:
        #     if "Already up to date." in stdout:
        #         embed.description = "Both image servers are up to date"
        #     else:
        #         embed.description = "Pull failed: Fast-forward strategy failed.  Look at logs for more details."
        #         ctx.bot.logger.warning(stdout)
        #     embed.description += addendum
        #     await ctx.send(embed=embed)
        #     return
        # embed.description += addendum
        # await ctx.send(embed=embed)


    @check_gymauth()
    @commands.hybrid_command()
    async def tradable(self, ctx, pokeid: int, answer: bool):
        """MOD: Set pokemon trade-able or not"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET tradable = $1 WHERE id = $2",
                answer,
                pokeid,
            )
        await ctx.send(f"Successfully set trade-able to {answer}")

    @check_admin()
    @commands.hybrid_command()
    async def setstats(self, ctx, id: int, hp: int, atk: int, defe: int, spatk: int, spdef: int, speed: int):
        """ADMIN: Set stats"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("call newstats($1,$2,$3,$4,$5,$6,$7)", id, hp, atk, defe, spatk, spdef, speed)
            await ctx.send(f"```Successfully set stats```")
    
    @check_investigator()
    @commands.hybrid_command()
    async def ownedservers(self, ctx, u_id: int):
        """INVEST: View the servers shared with mewbot that a user is the owner in."""
        launcher_res = await self.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            await ctx.send("I can't process that request right now, try again later.")
            return
        processes = len(launcher_res[0])
        body = (
            "result = []\n"
            "for guild in bot.guilds:\n"
            f"  if guild.owner_id == {u_id}:\n"
            "    result.append({'name': guild.name, 'id': guild.id, 'members': guild.member_count})\n"
            "return result"
        )
        eval_res = await self.bot.handler(
            "_eval", processes, args={"body": body, "cluster_id": "-1"}, scope="bot", _timeout=5
        )
        if not eval_res:
            await ctx.send("I can't process that request right now, try again later.")
            return
        data = []
        for response in eval_res:
            if response["message"]:
                data.extend(ast.literal_eval(response["message"]))
        pages = []
        for guild_data in data:
            msg = (
                f"Guild Name:   {guild_data['name']}\n"
                f"Guild ID:     {guild_data['id']}\n"
                f"Member Count: {guild_data['members']}\n"
            )
            pages.append(f"```\n{msg}```")
        await MenuView(ctx, pages).start()

    @check_mod()
    @commands.group(aliases=["pn", "pnick"])
    async def pokenick(self, ctx):
        """MOD: Nickname Utilities"""
        pass
        
async def setup(bot):
    await bot.add_cog(Sky(bot))
