import asyncio
from collections import defaultdict
from contextlib import redirect_stdout
import datetime
import inspect
import io
import os
import re
import textwrap
import time
import traceback
from typing import Literal
from discord.ext import commands, tasks
import discord
from mewcogs.pokemon_list import LegendList
from mewcore import commondb
from mewutils.checks import (
    check_admin,
    check_gymauth,
    check_art_team,
    check_helper,
    check_investigator,
    check_mod,
    check_owner,
)
from mewutils.misc import ConfirmView, MenuView, pagify, STAFFSERVER
from pokemon_utils.utils import get_pokemon_info

GREEN = "\N{LARGE GREEN CIRCLE}"
YELLOW = "\N{LARGE YELLOW CIRCLE}"
RED = "\N{LARGE RED CIRCLE}"


class EvalContext:
    def __init__(self, interaction):
        self.interaction = interaction
        self.message = interaction.message
        self.bot = interaction.client
        self.author = interaction.user

    async def send(self, *args, **kwargs):
        await self.interaction.followup.send(*args, **kwargs)


class EvalModal(discord.ui.Modal, title="Evaluate Code"):
    body = discord.ui.TextInput(label="Code", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        start = time.time()

        startTime = datetime.datetime.now()

        ectx = EvalContext(interaction)

        env = {
            "ctx": ectx,
            "interaction": interaction,
            "bot": interaction.client,
            "channel": interaction.channel,
            "author": interaction.user,
            "guild": interaction.guild,
            "message": interaction.message,
            "source": inspect.getsource,
        }

        body = str(self.body)

        env.update(globals())

        stdout = io.StringIO()
        out = None

        await interaction.followup.send(f"**Code:**\n```py\n{body}```")

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        async def paginate_send(ctx, text: str):
            """Paginates arbatrary length text & sends."""
            last = 0
            pages = []
            for curr in range(0, len(text), 1980):
                pages.append(text[last:curr])
                last = curr
            pages.append(text[last : len(text)])
            pages = list(filter(lambda a: a != "", pages))
            for page in pages:
                await ctx.send(f"```py\n{page}```")

        try:
            exec(to_compile, env)
            total_time = datetime.datetime.now() - startTime
            end = time.time()
            total_time2 = end - start
        except Exception as e:
            await paginate_send(ectx, f"{e.__class__.__name__}: {e}")
            return await interaction.message.add_reaction("\u2049")  # x

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await paginate_send(ectx, f"{value}{traceback.format_exc()}")
            return await interaction.message.add_reaction("\u2049")  # x
        value = stdout.getvalue()
        if ret is None:
            if value:
                out = await paginate_send(ectx, str(value))
        else:
            out = await paginate_send(ectx, f"{value}{ret}")
        await interaction.message.add_reaction("\u2705")  # tick


class EvalView(discord.ui.View):
    def __init__(self, author: int, *args, **kwargs):
        self.modal = EvalModal()
        self.author = author
        super().__init__(timeout=120)

    @discord.ui.button(label="Click Here")
    async def click_here(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self.author != interaction.user.id:
            return await interaction.response.send_message(
                "You can't do this!", ephemeral=True
            )
        await interaction.response.send_modal(self.modal)
        self.stop()


class KittyCat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}
        self.safe_edb = ""
        if self.bot.cluster["id"] == 1:
            self.task = asyncio.create_task(self.store_lb())
        else:
            self.task = None

    async def cog_check(self, ctx):
        return ctx.guild.id == STAFFSERVER

    async def cog_before_invoke(self, ctx):
        try:
            await ctx.bot.get_partial_messageable(999442907465523220).send(
                f"CMD - {ctx.command}\n\n"
                f"ARGS - `{ctx.kwargs}`\n\n"
                f"Author - {ctx.author}"
            )
        except:
            raise ValueError("Might be on Debug Mode")
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

    async def load_bans_cross_cluster(self):
        launcher_res = await self.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return
        processes = len(launcher_res[0])
        body = "await bot.load_bans()"
        await self.bot.handler(
            "_eval",
            processes,
            args={"body": body, "cluster_id": "-1"},
            scope="bot",
            _timeout=10,
        )

    @commands.hybrid_group()
    @discord.app_commands.guilds(STAFFSERVER)
    async def owner(self, ctx):
        """Owner-only commands."""
        pass

    @check_owner()
    @discord.app_commands.describe(
        extension_name="The name of the extension to reload."
    )
    @owner.command(name="reload")
    async def _owner_reload(self, ctx, extension_name: str):
        """Reloads an extension."""
        if "mew.cogs" in extension_name:
            extension_name = extension_name.replace("mew.cogs", "mewcogs")
        if not extension_name.startswith("mewcogs."):
            extension_name = f"mewcogs.{extension_name}"

        launcher_res = await ctx.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return await ctx.send(
                f"Launcher did not respond.  Please start with the launcher to use this command across all clusters.  If attempting to reload on this cluster alone, please use `{ctx.prefix}reloadsingle {extension_name}`"
            )

        messages = {}

        processes = len(launcher_res[0])
        # We don't really care whether or not it fails to unload... the main thing is just to get it loaded with a refresh
        await ctx.bot.handler(
            "unload", processes, args={"cogs": [extension_name]}, scope="bot"
        )
        load_res = await ctx.bot.handler(
            "load", processes, args={"cogs": [extension_name]}, scope="bot"
        )
        load_res.sort(key=lambda x: x["cluster_id"])

        e = discord.Embed(color=0xFFB6C1)
        builder = ""
        message_same = (
            all(
                [
                    load_res[0]["cogs"][extension_name]["message"]
                    == nc["cogs"][extension_name]["message"]
                    for nc in load_res
                ]
            )
            and load_res[0]["cogs"][extension_name]["message"]
        )
        if message_same:
            e.description = f"Failed to reload package on all clusters:\n`{load_res[0]['cogs'][extension_name]['message']}`"
        else:
            for cluster in load_res:
                if cluster["cogs"][extension_name]["success"]:
                    builder += (
                        f"`Cluster #{cluster['cluster_id']}`: Successfully reloaded\n"
                    )
                else:
                    msg = cluster["cogs"][extension_name]["message"]
                    builder += f"`Cluster #{cluster['cluster_id']}`: {msg}\n"
            e.description = builder

        class FSnow:
            def __init__(self, id):
                self.id = id

        await ctx.send("Syncing Commands...")
        # await ctx.bot.tree.sync()
        await ctx.bot.tree.sync(guild=FSnow(STAFFSERVER))
        await ctx.send("Successfully Synced.")
        await ctx.send(embed=e)

    @check_owner()
    @owner.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def addupdate(self, ctx, *, update):
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO updates (update, dev) VALUES ($1, $2)",
                update,
                ctx.author.mention,
            )
        await ctx.send("Update Successfully Added")

    @check_owner()
    @owner.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def traceback(self, ctx, public: bool = False):
        if not ctx.bot.traceback:
            await ctx.send("No exception has occurred yet.")
            return

        def paginate(text: str):
            """Simple generator that paginates text."""
            last = 0
            pages = []
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != "", pages))

        if public:
            destination = ctx.channel
        else:
            destination = ctx.author

        for page in paginate(ctx.bot.traceback):
            await destination.send("```py\n" + page + "```")

    @check_admin()
    @commands.hybrid_group()
    @discord.app_commands.guilds(STAFFSERVER)
    async def bb(self, ctx): ...

    @check_investigator()
    @bb.command(name="add")
    @discord.app_commands.guilds(STAFFSERVER)
    async def addbb(self, ctx, id: discord.User):
        """INVESTIGATOR: Ban specified user from using the bot in any server."""
        id = id.id
        banned = set(ctx.bot.banned_users)
        if id in banned:
            await ctx.send("That user is already botbanned!")
            return
        banned.add(id)
        await ctx.bot.mongo_update("blacklist", {}, {"users": list(banned)})
        await ctx.send(
            f"```Elm\n-Successfully Botbanned {await ctx.bot.fetch_user(id)}```"
        )
        await self.load_bans_cross_cluster()

    @check_investigator()
    @bb.command(name="remove")
    @discord.app_commands.guilds(STAFFSERVER)
    async def removebb(self, ctx, id: discord.User):
        """INVESTIGATOR: Unban specified user from the bot, allowing use of commands again"""
        id = id.id
        banned = set(ctx.bot.banned_users)
        if id not in banned:
            await ctx.send("That user is not botbanned!")
            return
        banned.remove(id)
        await ctx.bot.mongo_update("blacklist", {}, {"users": list(banned)})
        await ctx.send(
            f"```Elm\n- Successfully Unbotbanned {await ctx.bot.fetch_user(id)}```"
        )
        await self.load_bans_cross_cluster()

    @check_mod()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def spcount(self, ctx, userid: discord.Member):
        """MOD: Returns a users special pokemon counts, such as shiny and radiant"""
        async with ctx.bot.db[0].acquire() as pconn:
            shiny = await pconn.fetchval(
                "select count(*) from pokes where shiny = true AND id in (select unnest(u.pokes) from users u where u.u_id = $1)",
                userid.id,
            )
            radiant = await pconn.fetchval(
                "select count(*) from pokes where radiant = true AND id in (select unnest(u.pokes) from users u where u.u_id = $1)",
                userid.id,
            )
        embed = discord.Embed()
        embed.add_field(name="Number of Shiny pokemon", value=f"{shiny}", inline=True)
        embed.add_field(
            name="Number of Radiant pokemon", value=f"{radiant}", inline=False
        )
        embed.set_footer(text="Special Pokemon Counts")
        await ctx.send(embed=embed)

    @check_investigator()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
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
    @discord.app_commands.guilds(STAFFSERVER)
    async def donations(self, ctx, userid: discord.Member):
        """INVESTIGATOR: Shows a users total recorded donations from ;donate command only"""
        async with ctx.bot.db[0].acquire() as pconn:
            money = await pconn.fetchval(
                "select sum(amount) from donations where u_id = $1", userid.id
            )
        await ctx.send(money or "0")

    @check_mod()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def whoowns(self, ctx, poke: int):
        """MOD: Shows who owns a specific pokemon by its global ID"""
        async with ctx.bot.db[0].acquire() as pconn:
            user = await pconn.fetch(
                "SELECT u_id FROM users WHERE $1 = ANY(pokes)", poke
            )
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
    @discord.app_commands.guilds(STAFFSERVER)
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
    @discord.app_commands.guilds(STAFFSERVER)
    async def dupecheck(self, ctx, user_id: discord.Member):
        """ADMIN: Check a user to see if any of their pokemon have more than one owner."""
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
    @discord.app_commands.guilds(STAFFSERVER)
    async def addpoke(self, ctx, userid: discord.Member, poke: int):
        """INVESTIGATOR: Add a pokemon by its ID to a user by their userID"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2",
                poke,
                userid.id,
            )
        await ctx.send("Successfully added the pokemon to the user specified.")

    @check_investigator()
    @commands.hybrid_command(aliases=("yoink", "rob", "take", "steal"))
    @discord.app_commands.guilds(STAFFSERVER)
    async def removepoke(self, ctx, userid: discord.Member, poke: int):
        """INVESTIGATOR: Remove a pokemon by its ID to a user by their userID"""
        try:
            await ctx.bot.commondb.remove_poke(userid.id, poke)
        except commondb.UserNotStartedError:
            await ctx.send("That user has not started!")
            return
        await ctx.send("Successfully removed the pokemon from users pokemon array")

    @check_helper()
    @commands.hybrid_command(aliases=["gi"])
    @discord.app_commands.guilds(STAFFSERVER)
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

    @check_gymauth()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
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
    @discord.app_commands.guilds(STAFFSERVER)
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
                "UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = 1227",
                poke,
            )
        await ctx.send(f"User `1227` now owns poke `{poke}`.")

    @check_mod()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
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
            for id_ in await ctx.bot.redis_manager.redis.execute_command(
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
            msg += f"The pokemon from the listing was deleted for the following listings: `{data}`\n"
        if types.count("LowBal"):
            data = ", ".join([str(x[1]) for x in results if x[0] == "LowBal"])
            msg += f"You could not afford the following listings: `{data}`\n"
        if types.count("Error"):
            data = ", ".join(
                [str(x[1]) for x in results if isinstance(x[0], Exception)]
            )
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
        await ctx.bot.redis_manager.redis.execute_command(
            "LPUSH", "marketlock", str(listing_id)
        )
        try:
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetchrow(
                    "SELECT poke, owner, price, buyer FROM market WHERE id = $1",
                    listing_id,
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
                    "UPDATE market SET buyer = $1 WHERE id = $2",
                    ctx.author.id,
                    listing_id,
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
            await ctx.bot.redis_manager.redis.execute_command(
                "LREM", "marketlock", "1", str(listing_id)
            )
        return (None, None)

    @check_mod()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def refreshpatreons(self, ctx):
        """MOD: Refresh the patreon tier cache"""
        await ctx.bot.redis_manager.redis.execute_command(
            "SET", "patreonreset", time.time() + (60 * 15)
        )
        data = await ctx.bot._fetch_patreons()
        # Expand the dict, since redis doesn't like dicts
        result = []
        for k, v in data.items():
            result += [k, v]
        await ctx.bot.redis_manager.redis.execute_command("DEL", "patreontier")
        await ctx.bot.redis_manager.redis.execute_command("HMSET", "patreontier", *result)
        await ctx.send("Refreshed.")

    @commands.hybrid_group(name="mewstats")
    @discord.app_commands.guilds(STAFFSERVER)
    async def mew_stats(self, ctx):
        """HELPER: Base command"""
        ...

    @check_helper()
    @mew_stats.command(name="db")
    @discord.app_commands.guilds(STAFFSERVER)
    async def db(self, ctx):
        """HELPER: Show database statistics"""
        desc = "**__Subcommands:__**\n"
        for command in ctx.command.commands:
            desc += f"{ctx.prefix}{command.qualified_name}\n"
        embed = discord.Embed(description=desc, color=ctx.bot.get_random_color())
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def radiantot(self, ctx):
        """HELPER: Show radiant OT statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select caught_by, count(caught_by) from pokes where radiant = true group by caught_by order by count desc limit 25"
            )
        result = "\n".join([f'{x["count"]} | {x["caught_by"]}' for x in data])
        embed = discord.Embed(
            title="***Radiant pokemon by Original Trainer***",
            description=f"```{result}```",
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def radiantcount(self, ctx):
        """HELPER: Show radiant count statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select count(*), pokname from pokes where skin = 'radiant' group by pokname order by count desc"
            )
        desc = "\n".join([f'{x["count"]} | {x["pokname"]}' for x in data])
        pages = pagify(desc, base_embed=discord.Embed(title="***Radiant Counts***"))
        await MenuView(ctx, pages).start()

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def gleamcount(self, ctx):
        """HELPER: Show gleam count statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select count(*), pokname from pokes where skin = 'gleam' group by pokname order by count desc"
            )
        desc = "\n".join([f'{x["count"]} | {x["pokname"]}' for x in data])
        pages = pagify(desc, base_embed=discord.Embed(title="***Gleam Counts***"))
        await MenuView(ctx, pages).start()

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def shinyot(self, ctx):
        """HELPER: Show shiny OT statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select caught_by, count(caught_by) from pokes where shiny = true group by caught_by order by count desc limit 25"
            )
        result = "\n".join([f'{x["count"]} | {x["caught_by"]}' for x in data])
        embed = discord.Embed(
            title="Shiny pokemon by Original Trainer", description=f"```{result}```"
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def shinyrare(self, ctx):
        """HELPER: Show shiny rare count statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select count(*), pokname from pokes where shiny = true group by pokname order by count asc limit 25"
            )
        result = "\n".join([f'{x["count"]} | {x["pokname"]}' for x in data])
        embed = discord.Embed(
            title="Top 25 Rarest Shiny pokemon", description=f"```{result}```"
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def shinycommon(self, ctx):
        """HELPER: Show shiny count statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select count(*), pokname from pokes where shiny = true group by pokname order by count desc limit 25"
            )
        result = "\n".join([f'{x["count"]} | {x["pokname"]}' for x in data])
        embed = discord.Embed(
            title="Top 25 Most Common Shiny pokemon", description=f"```{result}```"
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def all_ot(self, ctx):
        """HELPER: Show all OT statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "select caught_by, count(caught_by) from pokes group by caught_by order by count desc limit 25"
            )
        result = "\n".join([f'{x["count"]} | {x["caught_by"]}' for x in data])
        embed = discord.Embed(
            title="Pokemon by Original Trainer", description=f"```{result}```"
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def legend_ot(self, ctx):
        """HELPER: Show legend OT statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "SELECT caught_by, count(caught_by) FROM pokes WHERE pokname = ANY($1) group by caught_by order by count desc LIMIT 25",
                LegendList,
            )
        result = "\n".join([f'{x["count"]} | {x["caught_by"]}' for x in data])
        embed = discord.Embed(
            title="**Legendary Pokemon by Original Trainer**",
            description=f"```{result}```",
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    @check_helper()
    @mew_stats.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def penta_ot(self, ctx):
        """HELPER: Show penta OT statistics"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "SELECT caught_by, count(caught_by) FROM (SELECT caught_by, (div(atkiv, 31) + div(defiv, 31) + div(hpiv, 31) + div(speediv, 31) + div(spdefiv, 31) + div(spatkiv, 31))::int as perfects FROM pokes) data WHERE perfects = 5 group by caught_by order by count desc limit 25",
                timeout=30.0,
            )
        result = "\n".join([f'{x["count"]} | {x["caught_by"]}' for x in data])
        embed = discord.Embed(
            title="Top 25 Pentas by Original Trainer", description=f"```{result}```"
        )
        embed.set_footer(text="Mewbot Statistics")
        await ctx.send(embed=embed)

    # @check_helper()
    # @mew_stats.command()
    # @discord.app_commands.guilds(STAFFSERVER)
    # async def lb_chests(self, ctx):
    #     """HELPER: Show leading chest statistics"""
    #     async with ctx.bot.db[0].acquire() as pconn:
    #         data = await pconn.fetch("select count(args), u_id from skylog where args = ';open legend' group by u_id order by count desc limit 30")
    #     result = '\n'.join([f'{x["count"]} | {x["u_id"]}' for x in data])
    #     embed = discord.Embed(title="***Chests Opened Leaderboard***", description=f"```{result}```")
    #     embed.set_footer(text="Mewbot Statistics")
    #     await ctx.send(embed=embed)

    @check_admin()
    @commands.hybrid_group()
    @discord.app_commands.guilds(STAFFSERVER)
    async def gib(self, ctx): ...

    @check_admin()
    @gib.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def streak(
        self, ctx, user: discord.Member, type: Literal["shadow", "vote"], amount: int
    ):
        """Give Shadow or Vote Streaks to a user"""

        async with ctx.bot.db[0].acquire() as pconn:
            if type == "vote":
                await pconn.execute(
                    "UPDATE users SET last_vote = $1, vote_streak = vote_streak + $2 WHERE u_id = $3",
                    int(time.time()),
                    amount,
                    user.id,
                )
            elif type == "shadow":
                await pconn.execute(
                    "UPDATE users SET chain = chain + $1 WHERE u_id = $2",
                    amount,
                    user.id,
                )
            embed = discord.Embed(
                title="Success!",
                description=f"{user} Got {amount} {type} streak points.",
            )
            embed.set_footer(text="Definitely hax... lots of hax")
            await ctx.send(embed=embed)

    @check_gymauth()
    @gib.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def redeems(self, ctx, user: discord.Member, amount: int):
        """Give Redeems to a user"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $1 where u_id = $2",
                amount,
                user.id,
            )
            embed = discord.Embed(
                title="Success!", description=f"{user} Got {amount} redeems."
            )
            embed.set_footer(text="Definitely hax... lots of hax")
            await ctx.send(embed=embed)

    @check_admin()
    @gib.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def credits(self, ctx, user: discord.Member, amount: int):
        """Give credits to a user"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 where u_id = $2",
                amount,
                user.id,
            )
            embed = discord.Embed(
                title="Success!", description=f"{user} Got {amount} credits."
            )
            embed.set_footer(text="Definitely hax... lots of hax")
            await ctx.send(embed=embed)

    @check_admin()
    @gib.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def gems(self, ctx, user: discord.Member, gems: int):
        """Give Gems to a user."""
        await ctx.bot.commondb.add_bag_item(user.id, "radiant_gem", gems, True)
        embed = discord.Embed(
            title="Success!", description=f"{user} gained {gems} radiant gem(s)"
        )
        embed.set_footer(text="Definitely hax... lots of hax")
        await ctx.send(embed=embed)

    @check_investigator()
    @commands.hybrid_command(aliases=["serverban"])
    async def banserver(self, ctx, id):
        id = int(id)
        """INVESTIGATOR: Ban a server"""
        sbans = set(ctx.bot.banned_guilds)
        if id in sbans:
            await ctx.send("That server is already banned.")
            return
        sbans.add(id)
        await ctx.bot.mongo_update("blacklist", {}, {"guilds": list(sbans)})
        await ctx.send(
            f"```Elm\n-Successfully Banned {await ctx.bot.fetch_guild(id)}```"
        )
        await self.load_bans_cross_cluster()

    @check_investigator()
    @commands.hybrid_command(aliases=["serverunban", "unserverban"])
    async def unbanserver(self, ctx, id):
        """INVESTIGATOR: UNBan a server"""
        id = int(id)
        sbans = set(ctx.bot.banned_guilds)
        if id not in sbans:
            await ctx.send("That server is not banned.")
            return
        sbans.remove(id)
        await ctx.bot.mongo_update("blacklist", {}, {"guilds": list(sbans)})
        await ctx.send(
            f"```Elm\n- Successfully Unbanned {await ctx.bot.fetch_guild(id)}```"
        )
        await self.load_bans_cross_cluster()

    @check_gymauth()
    @gib.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def chest(
        self,
        ctx,
        user: discord.Member,
        chest: Literal[
            "legend chest",
            "mythic chest",
            "rare chest",
            "common chest",
            "art chest",
            "pat chest",
        ],
        amount: int = 1,
    ):
        """Add a chest"""
        if "pat" in chest and ctx.author.id != 455277032625012737:
            return
        user_id = int(user.id)
        await ctx.bot.commondb.add_bag_item(
            user_id, chest.replace(" ", "_"), amount, True
        )
        await ctx.send(f"<@{user_id}> gained `{amount}` `{chest}'s`")

    @check_mod()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def wss(self, ctx):
        response = await ctx.bot.http.request(discord.http.Route("GET", "/gateway/bot"))
        await ctx.send(f"```py\n{response}```")

    @check_admin()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def clusters(self, ctx):
        launcher_res = await ctx.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return await ctx.send(
                "Launcher did not respond.  Please start with the launcher to use this command."
            )

        processes = len(launcher_res[0])
        process_res = await ctx.bot.handler("send_cluster_info", processes, scope="bot")

        process_res.sort(key=lambda x: x["id"])

        pages = []
        current = None
        count = 1
        for cluster in process_res:
            if cluster["id"] % 3 == 1 or not current:
                if current:
                    pages.append(current)
                current = discord.Embed(
                    title=f"Clusters {cluster['id']} - {cluster['id'] + 2}",
                    color=0xFFB6C1,
                )
                current.set_footer(
                    text=f"{ctx.prefix}[ n|next, b|back, s|start, e|end ]"
                )
                count += 1
            msg = (
                "```prolog\n"
                f"Latency:    {cluster['latency']}ms\n"
                f"Shards:     {cluster['shards'][0]}-{cluster['shards'][-1]}\n"
                f"Guilds:     {cluster['guilds']}\n"
                f"Channels:   {cluster['channels']}\n"
                f"Users:      {cluster['users']}\n"
                "```"
            )
            current.add_field(
                name=f"Cluster #{cluster['id']} ({cluster['name']})", value=msg
            )

        current.title = current.title[: -len(str(cluster["id"]))] + str(cluster["id"])
        pages.append(current)

        embed = await ctx.send(embed=pages[0])
        current_page = 1

        def get_value(message):
            return {
                f"{ctx.prefix}n": min(len(pages), current_page + 1),
                f"{ctx.prefix}next": min(len(pages), current_page + 1),
                f"{ctx.prefix}b": max(1, current_page - 1),
                f"{ctx.prefix}back": max(1, current_page - 1),
                f"{ctx.prefix}e": len(pages),
                f"{ctx.prefix}end": len(pages),
                f"{ctx.prefix}s": 1,
                f"{ctx.prefix}start": 1,
            }.get(message)

        commands = (
            f"{ctx.prefix}n",
            f"{ctx.prefix}next",
            f"{ctx.prefix}back",
            f"{ctx.prefix}b",
            f"{ctx.prefix}e",
            f"{ctx.prefix}end",
            f"{ctx.prefix}s",
            f"{ctx.prefix}start",
        )

        while True:
            try:
                message = await ctx.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author
                    and m.content.lower() in commands,
                    timeout=60,
                )
            except asyncio.TimeoutError:
                break

            try:
                await message.delete()
            except:
                pass

            current_page = get_value(message.content.lower())
            await embed.edit(embed=pages[current_page - 1])

    @check_mod()
    @commands.group(aliases=["pn", "pnick"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def pokenick(self, ctx):
        """MOD: Nickname Utilities"""
        pass

    @check_admin()
    @pokenick.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def change(self, ctx, *, search_term: str):
        """ADMIN: Change all pokemon nicknames that meet your search"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetchval(
                "SELECT count(*) FROM pokes WHERE poknick like $1", search_term
            )
        counttext = f'{data["count"]} pokemon nicknames will be changed, are you sure you wish to do this?'
        await ctx.send(f"{counttext}")

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
        warning = "Nickname Violation"
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET poknick = $2 WHERE poknick like $1",
                search_term,
                warning,
            )
        await ctx.send(
            f"Changed {counttext} pokemon nicknames to `Nickname Violation`."
        )

    @check_gymauth()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def gymcalc(self, ctx, chan: str, messageid: str):
        chan, messageid = int(chan), int(messageid)
        winrate = defaultdict(int)
        lossrate = defaultdict(int)
        leaders = set()
        async for m in ctx.guild.get_channel(chan).history(
            after=discord.Object(messageid), limit=None
        ):
            leaders.add(m.author)
            if "lost" in m.content:
                winrate[m.author] += 1
            if "won" in m.content or "beat" in m.content:
                lossrate[m.author] += 1

        result = []
        for leader in leaders:
            games = winrate[leader] + lossrate[leader]
            if games == 0:
                continue
            percent = round((winrate[leader] / games) * 100, 2)
            result.append([leader, percent, games])
        result.sort(key=lambda a: a[1], reverse=True)
        msg = ""
        for val in result:
            msg += f"**{val[0]}** | `{val[2]} battles`\n> `{val[1]}% win rate`\n"
        await ctx.send(ctx.author.mention)
        embed = discord.Embed(title="NAME - WIN% - TOTAL BATTLES", description=msg)
        await ctx.send(embed=embed)

    @check_gymauth()
    @commands.hybrid_command(aliases=["gymstat"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def gym_stats(self, ctx):
        roles = [
            931549759104221215,
            909542667774480424,
            931479318297739344,
            857746524527001611,
            857746524527001616,
            857746524527001618,
        ]
        a = ""
        for role in roles:
            role = ctx.guild.get_role(role)
            if role is None:
                continue
            count = len(role.members)
            a += f"{role.name} - {count}\n"

        b = discord.Embed(
            title=f"members in {ctx.guild.name}",
            description=a,
            color=discord.Color((0xFFFF00)),
        )
        await ctx.send(embed=b)

    @check_investigator()
    @commands.hybrid_group(aliases=["r", "repo"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def repossess(self, ctx):
        """INVESTIGATOR: COMMANDS FOR REPOSSESSING THINGS FROM OFFENDERS"""
        pass

    @check_investigator()
    @repossess.command(aliases=["c", "bread", "cheese"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def credits(self, ctx, user: discord.Member, val: int):
        """INVESTIGATOR: REPOSSESS CREDITS"""
        if ctx.author.id == user.id:
            await ctx.send(
                "<:err:997377264511623269>!:\nYou cant take your own credits!"
            )
            return
        if val <= 0:
            await ctx.send(
                "<:err:997377264511623269>!:\nYou need to transfer at least 1 credit!"
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            giver_creds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", user.id
            )
            getter_creds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = 123"
            )

        if getter_creds is None:
            await ctx.send(f"<:err:997377264511623269>!:\nIssue with fake UserID (123)")
            return
        if giver_creds is None:
            await ctx.send(
                f"<:err:997377264511623269>!:\n{user.name}({user.id}) has not started."
            )
            return
        if val > giver_creds:
            await ctx.send(
                f"<:err:997377264511623269>!:\n{user.name}({user.id}) does not have that many credits!"
            )
            return
        if not await ConfirmView(
            ctx,
            f"Are you sure you want to move **{val}** credits from **{user.name}**({user.id}) to **Mewbot's Central Bank?**",
        ).wait():
            await ctx.send("<:err:997377264511623269>!:\nTransfer **Cancelled.**")
            return

        async with ctx.bot.db[0].acquire() as pconn:
            curcreds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", user.id
            )
            if val > curcreds:
                await ctx.send(
                    "<:err:997377264511623269>!:\nUser does not have that many credits anymore..."
                )
                return
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                val,
                user.id,
            )
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = 123",
                val,
            )
            await ctx.send(
                f"{val} Credits taken from {user.name}({user.id}), added to fake u_id `123`."
            )
            await ctx.bot.get_partial_messageable(999442907465523220).send(
                f"<:err:997377264511623269>-Staff Member: {ctx.author.name}-``{ctx.author.id}``\nCredits Taken From: {user.name}-`{user.id}`\nAmount: ```{val} credits```\n"
            )
            # await pconn.execute(
            #    "INSERT INTO trade_logs (sender, receiver, sender_credits, command, time) VALUES ($1, $2, $3, $4, $5) ",
            #    ctx.author.id, user.id, val, "repo", datetime.now()
            # )

    @check_investigator()
    @repossess.command(aliases=["d", "deems", "r"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def redeems(self, ctx, user: discord.Member, val: int):
        """INVESTIGATOR: REPOSSESS REDEEMS"""
        if ctx.author.id == user.id:
            await ctx.send(
                "<:err:997377264511623269>!:\nYou cant take your own Redeems!"
            )
            return
        if val <= 0:
            await ctx.send(
                "<:err:997377264511623269>!:\nYou need to transfer at least 1 Redeem!"
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            giver_creds = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = $1", user.id
            )
            getter_creds = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = 123"
            )

        if getter_creds is None:
            await ctx.send(f"<:err:997377264511623269>!:\nIssue with fake UserID (123)")
            return
        if giver_creds is None:
            await ctx.send(
                f"<:err:997377264511623269>!:\n{user.name}({user.id}) has not started."
            )
            return
        if val > giver_creds:
            await ctx.send(
                f"<:err:997377264511623269>!:\n{user.name}({user.id}) does not have that many redeems!!"
            )
            return
        if not await ConfirmView(
            ctx,
            f"Are you sure you want to move **{val}** redeems from\n**{user.name}**({user.id})\nto **Mewbot's Central Bank?**",
        ).wait():
            await ctx.send("<:err:997377264511623269>!:\nTransfer **Cancelled.**")
            return

        async with ctx.bot.db[0].acquire() as pconn:
            curcreds = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = $1", user.id
            )
            if val > curcreds:
                await ctx.send(
                    "<:err:997377264511623269>!:\nUser does not have that many redeems anymore..."
                )
                return
            await pconn.execute(
                "UPDATE users SET redeems = redeems - $1 WHERE u_id = $2",
                val,
                user.id,
            )
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $1 WHERE u_id = 123",
                val,
            )
            await ctx.send(
                f"{val} redeems taken from {user.name}({user.id}), added to fake u_id `123`."
            )
            await ctx.bot.get_partial_messageable(999442907465523220).send(
                f"<:err:997377264511623269>-Staff Member: {ctx.author.name}-``{ctx.author.id}``\nredeems Taken From: {user.name}-`{user.id}`\nAmount: ```{val} redeems```\n"
            )
            # await pconn.execute(
            #    "INSERT INTO trade_logs (sender, receiver, sender_credits, command, time) VALUES ($1, $2, $3, $4, $5) ",
            #    ctx.author.id, user.id, val, "repo", datetime.now()
            # )

    @check_investigator()
    @repossess.command(aliases=["a", "everything"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def all(self, ctx, user: discord.Member):
        """INVESTIGATOR: REPOSSESS EVERYTHING"""
        if ctx.author.id == user.id:
            await ctx.send("<:err:997377264511623269>!: You cant take your own stuff!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            giver_creds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", user.id
            )
            getter_creds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = 123"
            )

        if getter_creds is None:
            await ctx.send(f"<:err:997377264511623269>!: Issue with fake UserID (123)")
            return
        if giver_creds is None:
            await ctx.send(
                f"<:err:997377264511623269>!: {user.name}({user.id}) has not started."
            )
            return
        if not await ConfirmView(
            ctx,
            f"Are you sure you want to move all **REDEEMS AND CREDITS** from\n**{user.name}**({user.id})\nto **Mewbot's Central Bank?**",
        ).wait():
            await ctx.send("<:err:997377264511623269>!:\nTransfer **Cancelled.**")
            return

        async with ctx.bot.db[0].acquire() as pconn:
            curcreds = await pconn.fetchrow(
                "SELECT mewcoins, redeems FROM users WHERE u_id = $1", user.id
            )
            credits = curcreds["mewcoins"]
            redeems = curcreds["redeems"]
            await pconn.execute(
                "UPDATE users SET redeems = redeems = 0, mewcoins = 0 WHERE u_id = $1",
                user.id,
            )
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $1, mewcoins = mewcoins + $2 WHERE u_id = 123",
                redeems,
                credits,
            )
            await ctx.send(
                f"{redeems} redeems\n{credits} credits\ntaken from {user.name}({user.id}), added to fake u_id `123`."
            )
            await ctx.bot.get_partial_messageable(999442907465523220).send(
                f"<:err:997377264511623269>-Staff Member: {ctx.author.name}-``{ctx.author.id}``\nEVERYTHING Taken From: {user.name}-`{user.id}`\nAmount: ```{credits} credits\n{redeems} redeems```\n"
            )
            # await pconn.execute(
            #    "INSERT INTO trade_logs (sender, receiver, sender_credits, command, time) VALUES ($1, $2, $3, $4, $5) ",
            #    ctx.author.id, user.id, val, "repo", datetime.now()
            # )

    @check_investigator()
    @repossess.command(aliases=["b", "balance"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def bank(self, ctx):
        """INVESTIGATOR: BANK BALANCES"""
        async with ctx.bot.db[0].acquire() as pconn:
            redeems = await pconn.fetchval("SELECT redeems FROM users WHERE u_id = 123")
            mewcoins = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = 123"
            )
        embed = discord.Embed(title="Balances", color=0xFF0000)
        embed.set_author(
            name="Mewbot Central Bank",
            url=f"https://discord.com/channels/{os.environ['OFFICIAL_SERVER']}/793744327746519081/",
        )
        embed.set_thumbnail(
            url="https://bot.to/wp-content/uploads/edd/2020/09/d5a4713693a852257ca24ec8d251e295.png"
        )
        embed.add_field(name="Total Credits:", value=f"{mewcoins}", inline=False)
        embed.add_field(name="Total Redeems:", value=f"{redeems}", inline=False)
        embed.set_footer(text="All credits/redeems are from Bot-banned Users")
        await ctx.send(embed=embed)

    @check_investigator()
    @repossess.command(aliases=["h", "info"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def help(self, ctx):
        """INVESTIGATOR: COMMANDS"""
        embed = discord.Embed(
            title="Repossess Command",
            description="**Base Command:** `;repossess <sub-command>`\n**Aliases:** `;r`",
            color=0xFF0000,
        )
        embed.set_author(
            name="Investigation Team Only",
            url="https://discord.com/channels/519466243342991360/793744327746519081/",
            icon_url="https://static.thenounproject.com/png/3022281-200.png",
        )
        embed.set_thumbnail(
            url="https://bot.to/wp-content/uploads/edd/2020/09/d5a4713693a852257ca24ec8d251e295.png"
        )
        embed.add_field(
            name=";r redeems <user id> <amount>",
            value="Moves redeems to bank\n**Aliases**: `r, d, deems`",
            inline=False,
        )
        embed.add_field(
            name=";r credits <user id> <amount>",
            value="Moves credits to bank\n**Aliases**: `c, bread, cheese`",
            inline=False,
        )
        embed.add_field(
            name=";r everything <user id>",
            value="Moves all redeems and credits to bank\n**Aliases**: `r, d, deems`",
            inline=True,
        )
        embed.set_footer(text="All commands are logged in support bot server!")
        await ctx.send(embed=embed)

    @check_admin()
    @commands.hybrid_group()
    @discord.app_commands.guilds(STAFFSERVER)
    async def demote(self, ctx):
        """ADMIN: Demote users."""
        pass

    @check_admin()
    @demote.command(name="staff")
    @discord.app_commands.guilds(STAFFSERVER)
    async def _demote_staff(self, ctx, member: discord.Member):
        """ADMIN: Demote a user from Staff."""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET staff = 'User' WHERE u_id = $1", member.id
            )

        msg = f"{GREEN} Removed bot permissions.\n"
        if ctx.guild != ctx.bot.official_server:
            msg += (
                f"{RED} Could not remove OS roles, as this command was not run in OS.\n"
            )
            await ctx.send(msg)
            return
        ranks = {
            "Support": ctx.guild.get_role(544630193449598986),
            "Trial": ctx.guild.get_role(809624282967310347),
            "Mod": ctx.guild.get_role(998224325159178301),
            "Investigator": ctx.guild.get_role(1009276177418043424),
            "Gymauth": ctx.guild.get_role(998398578420629515),
            "Admin": ctx.guild.get_role(998147456959270943),
        }
        removeset = set(ranks.values())
        currentset = set(member.roles)
        removeset &= currentset
        if not removeset:
            msg += f"{YELLOW} User had no rank roles to remove.\n"
        else:
            removelist = list(removeset)
            await member.remove_roles(
                *removelist, reason=f"Staff demotion - {ctx.author}"
            )
            removelist = [str(x) for x in removelist]
            msg += (
                f"{GREEN} Removed existing rank role(s) **{', '.join(removelist)}.**\n"
            )

        staff_role = ctx.guild.get_role(1009277747677372458)
        if staff_role not in member.roles:
            msg += f"{YELLOW} User did not have the **{staff_role}** role.\n"
        else:
            await member.remove_roles(
                staff_role, reason=f"Staff demotion - {ctx.author}"
            )
            msg += f"{GREEN} Removed the **{staff_role}** role.\n"

        await ctx.send(msg)

    @check_admin()
    @demote.command(name="gym")
    @discord.app_commands.guilds(STAFFSERVER)
    async def _demote_gym(self, ctx, user_id: discord.Member):
        """ADMIN: Demote a user from Gym Leader."""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET gym_leader = false WHERE u_id = $1", user_id.id
            )
        await ctx.send("Done.")

    @check_admin()
    @commands.hybrid_group()
    @discord.app_commands.guilds(STAFFSERVER)
    async def promote(self, ctx):
        """ADMIN: Promote users."""
        pass

    @check_admin()
    @promote.command(name="staff")
    @discord.app_commands.guilds(STAFFSERVER)
    async def _promote_staff(
        self,
        ctx,
        rank: Literal[
            "User",
            "Support",
            "Trial",
            "Mod",
            "Investigator",
            "Gymauth",
            "Admin",
            "Developer",
        ],
        member: discord.Member,
    ):
        """ADMIN: Promote a user to a Staff rank."""
        rank = rank.title()
        if rank not in (
            "User",
            "Support",
            "Trial",
            "Mod",
            "Investigator",
            "Gymauth",
            "Admin",
            "Developer",
        ):
            await ctx.send(f"{RED} Invalid rank.")
            return
        if rank == "Developer":
            await ctx.send(f"{RED} Cannot promote a user to Developer, do so manually.")
            return
        if rank == "User":
            await ctx.send(f"{RED} To demote a user, use `;demote staff`.")
            return

        if rank != "Trial":
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET staff = $2 WHERE u_id = $1", member.id, rank
                )
            msg = f"{GREEN} Gave bot permission level **{rank}**.\n"

        if ctx.guild.id != int(os.environ["OFFICIAL_SERVER"]):
            msg += f"{RED} Could not add or remove OS roles, as this command was not run in OS.\n"
            await ctx.send(msg)
            return

        ranks = {
            "Support": ctx.guild.get_role(544630193449598986),
            "Trial": ctx.guild.get_role(809624282967310347),
            "Mod": ctx.guild.get_role(998224325159178301),
            "Investigator": ctx.guild.get_role(1009276177418043424),
            "Gymauth": ctx.guild.get_role(998398578420629515),
            "Admin": ctx.guild.get_role(998147456959270943),
        }
        removeset = set(ranks.values())
        removeset.remove(ranks[rank])
        currentset = set(member.roles)
        removeset &= currentset
        if not removeset:
            msg += f"{YELLOW} User had no other rank roles to remove.\n"
        else:
            removelist = list(removeset)
            await member.remove_roles(
                *removelist, reason=f"Staff promotion - {ctx.author}"
            )
            removelist = [str(x) for x in removelist]
            msg += (
                f"{GREEN} Removed existing rank role(s) **{', '.join(removelist)}.**\n"
            )

        if ranks[rank] in member.roles:
            msg += f"{YELLOW} User already had the **{ranks[rank]}** role.\n"
        else:
            await member.add_roles(
                ranks[rank], reason=f"Staff promotion - {ctx.author}"
            )
            msg += f"{GREEN} Added new rank role **{ranks[rank]}**.\n"

        if rank != "Support":
            staff_role = ctx.guild.get_role(1009277747677372458)
            if staff_role in member.roles:
                msg += f"{YELLOW} User already had the **{staff_role}** role.\n"
            else:
                await member.add_roles(
                    staff_role, reason=f"Staff promotion - {ctx.author}"
                )
                msg += f"{GREEN} Added the **{staff_role}** role.\n"

        await ctx.send(msg)

    @check_admin()
    @promote.command(name="gym")
    @discord.app_commands.guilds(STAFFSERVER)
    async def _promote_gym(self, ctx, user_id: discord.Member):
        """ADMIN: Promote a user to Gym Leader."""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET gym_leader = true WHERE u_id = $1", user_id.id
            )
        await ctx.send("Done.")

    # @check_mod()
    # @commands.hybrid_command()
    async def modcmds(self, ctx):
        """MOD: Mod level commands. CURRENTLY DEPRECATED"""
        desc = ""
        desc += "`mewstats` - **Show different database statistics**\n"
        desc += "> `lb_chests` - **Show leading chest statistics**\n"
        desc += "> `radiantcount` - **Show radiant count statistics**\n"
        desc += "> `legend_ot` - **Show legend OT statistics**\n"
        desc += "> `radiantot` - **Show radiant OT statistics**\n"
        desc += "> `shinyrare` - **Show shiny rare count statistics**\n"
        desc += "> `shinyot` - **Show shiny OT statistics**\n"
        desc += "> `shinycommon` - **Show shiny count statistics**\n"
        desc += "> `all_ot` - **Show all OT statistics**\n"
        desc += "> `penta_ot` - **Show penta OT statistics**\n"
        desc += "`spcount` - **Returns a users special pokemon counts, such as shiny and radiant**\n"
        desc += "`getpoke` - **Get pokemon info by ID**\n"
        desc += "`findot` - **Find the OT userid of a pokemon**\n"
        desc += "`getuser` - **Get user info by ID**\n"
        desc += "`textsky` - **Send a text to sky**\n"
        desc += "`whoowns` - **Shows who owns a specific pokemon by its global ID**\n"
        desc += "`grantsupport` - **Promote a user to Support Team**\n"
        desc += "`refreshpatreons` - **Refresh the patreon tier cache**\n"
        desc += "`globalinfo` - **Info a poke using its global id.**\n"
        desc += "`mocksession` - **Same as mock, but toggled on and off for total mocking of a user id**\n"
        desc += "`mocksessionend` - **Ends the mocking session**\n"
        desc += "`mock` - **mock another user by ID**\n"
        desc += "`marketmany` - **Buy multiple pokes from the market at once.**\n"
        desc += "`marketinfo` - **Hidden info about marketed pokes.**\n"
        desc += "`tradable` - **Set pokemon trade-able or not**\n"
        embed = discord.Embed(title="Moderators", description=desc, color=0xFF0000)
        embed.set_author(name="Commands Usable by:")
        embed.set_footer(text="Use of these commands is logged in detail")
        await ctx.send(embed=embed)

    @check_mod()
    @pokenick.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def search(self, ctx, search_term: str):
        """MOD: Global Pokemon Nickname search"""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "SELECT * FROM pokes WHERE poknick like $1", search_term
            )
        msg = ""
        for x in data:
            msg += f'`{x["id"]} | {x["poknick"]}`\n'
        embed = discord.Embed(title="***GlobalID | Nickname***", color=0xDD00DD)
        pages = pagify(msg, per_page=20, base_embed=embed)
        await MenuView(ctx, pages).start()

    @check_admin()
    @pokenick.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def regex(self, ctx, search_term: str):
        """ADMIN: Global Pokemon Nickname search (REGEX)"""
        search_term_regex = f"^{search_term}$"
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetch(
                "SELECT * FROM pokes WHERE poknick ~ $1", search_term_regex
            )
        msg = ""
        for x in data:
            msg += f'`{x["id"]} | {x["poknick"]}`\n'
        embed = discord.Embed(title="***GlobalID | Nickname***", color=0xDD00DD)
        pages = pagify(msg, per_page=20, base_embed=embed)
        await MenuView(ctx, pages).start()

    @check_owner()
    @owner.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def _eval(self, ctx):
        """Evaluates python code"""
        await ctx.send(
            "Please click the below button to evaluate your code.",
            view=EvalView(ctx.author.id),
        )

    @check_owner()
    @owner.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def sync(self, ctx):
        """Syncs all commands with discord"""

        class FSnow:
            def __init__(self, id):
                self.id = id

        await ctx.send("syncing...")
        await ctx.bot.tree.sync()
        await ctx.bot.tree.sync(guild=FSnow(STAFFSERVER))
        await ctx.send("Successfully synced.")

    
    @check_owner()
    @owner.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def executedb(
        self,
        ctx: commands.Context,
        type: Literal["row", "fetch", "val", "execute"],
        execution: str,
    ):
        """Run SQL commands directly"""
        try:
            await ctx.bot.log(
                527031932110897152,
                f"{ctx.author.name} used edb - Execution = `{execution}`",
            )
        except:
            pass

        # Sanity checks
        low_exe = execution.lower()
        if low_exe != self.safe_edb:
            self.safe_edb = low_exe
            if "update" in low_exe and "where" not in low_exe:
                await ctx.send(
                    "**WARNING**: You attempted to run an `UPDATE` without a `WHERE` clause. If you are **absolutely sure** this action is safe, run this command again."
                )
                return
            if "drop" in low_exe:
                await ctx.send(
                    "**WARNING**: You attempted to run a `DROP`. If you are **absolutely sure** this action is safe, run this command again."
                )
                return
            if "delete from" in low_exe:
                await ctx.send(
                    "**WARNING**: You attempted to run a `DELETE FROM`. If you are **absolutely sure** this action is safe, run this command again."
                )
                return

        try:
            async with ctx.bot.db[0].acquire() as pconn:
                if type == "row":
                    result = await pconn.fetchrow(execution)
                elif type == "fetch":
                    result = await pconn.fetch(execution)
                elif type == "val":
                    result = await pconn.fetchval(execution)
                elif type == "execute":
                    result = await pconn.execute(execution)
        except Exception as e:
            await ctx.send(f"```py\n{e}```")
            raise

        result = str(result)
        if len(result) > 1950:
            result = result[:1950] + "\n\n..."
        await ctx.send(f"```py\n{result}```")

    async def get_commit(self, ctx):
        COMMAND = f"cd {ctx.bot.app_directory} && git branch -vv"

        proc = await asyncio.create_subprocess_shell(
            COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        stdout = stdout.decode().split("\n")

        for branch in stdout:
            if branch.startswith("*"):
                return branch

        raise ValueError()

    @check_admin()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def chdo(self, ctx, date: str = None):
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        except:
            await ctx.send(
                "Incorrect date format passed. Format must be, `;[ chdo ] YYYY-MM-DD`\n`;chdo 2021-04-10`"
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            result = await pconn.fetchval(
                "SELECT sum(amount) FROM donations WHERE date_donated >= $1", date
            )
            await ctx.author.send(f"{date} - {datetime.datetime.now()} = ${result}")

    @check_admin()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def refresh(self, ctx):
        COMMAND = f"cd {ctx.bot.app_directory} && git pull"
        addendum = ""

        proc = await asyncio.create_subprocess_shell(
            COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        stdout = stdout.decode()
        await ctx.send(stdout)
        if "no tracking information" in stderr.decode():
            COMMAND = f"cd {ctx.bot.app_directory} && git pull origin main"
            proc = await asyncio.create_subprocess_shell(
                COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            stdout = stdout.decode()
            addendum = "\n\n**Warning: no upstream branch is set.  I automatically pulled from origin/main but this may be wrong.  To remove this message and make it dynamic, please run `git branch --set-upstream-to=origin/<branch> <branch>`**"

        embed = discord.Embed(title="Git pull", description="", color=0xFFB6C1)

        if "Fast-forward" not in stdout:
            if "Already up to date." in stdout:
                embed.description = "Code is up to date from upstream remote"
            else:
                embed.description = "Pull failed: Fast-forward strategy failed.  Look at logs for more details."
                ctx.bot.logger.warning(stdout)
            embed.description += addendum
            await ctx.send(embed=embed)
            return

        cogs = []
        main_files = []

        try:
            current = await self.get_commit(ctx)
        except ValueError:
            pass
        else:
            embed.description += f"`{current[2:]}`\n"

        cogs = re.findall(r"\smew\/mewcogs\/(\w+)", stdout)
        if len(cogs) > 1:
            embed.description += f"The following cogs were updated and needs to be reloaded: `{'`, `'.join(cogs)}`.\n"
        elif len(cogs) == 1:
            embed.description += f"The following cog was updated and needs to be reloaded: `{cogs[0]}`.\n"
        else:
            embed.description += "No cogs were updated.\n"

        main_files = re.findall(r"\smew\/(?!mewcogs)(\S*)", stdout)
        if len(main_files) > 1:
            embed.description += f"The following non-cog files were updated and require a restart: `{'`, `'.join(main_files)}`."
        elif main_files:
            embed.description += f"The following non-cog file was updated and requires a restart: `{main_files[0]}`."
        else:
            embed.description += "No non-cog files were updated."

        callbacks = re.findall(r"\scallbacks\/(\w+)", stdout)
        if len(callbacks) > 1:
            embed.description += f"The following callback files were updated and require a docker build: `{'`, `'.join(callbacks)}`."
        elif callbacks:
            embed.description += f"The following callback file was updated and requires a docker build: `{callbacks[0]}`."

        duelapi = re.findall(r"\sduelapi\/(\w+)", stdout)
        if len(duelapi) > 1:
            embed.description += f"The following duel API files were updated and require a docker build: `{'`, `'.join(duelapi)}`."
        elif duelapi:
            embed.description += f"The following duel API file was updated and requires a docker build: `{duelapi[0]}`."

        embed.description += addendum

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(KittyCat(bot))
