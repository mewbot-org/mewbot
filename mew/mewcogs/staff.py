import discord
import random
from discord.ext import commands
import subprocess
from contextlib import suppress
import asyncio
import os

from discord.ui import Button, View
from typing import Literal
from discord.ext.commands.view import StringView
from discord.ext.commands.converter import (
    MemberConverter,
    TextChannelConverter,
    _convert_to_bool,
)
from mewcogs.json_files import *
from mewcogs.pokemon_list import *
from mewcogs.pokemon_list import _
from mewutils.checks import (
    check_admin,
    check_investigator,
    check_mod,
    check_helper,
    check_gymauth,
)
from mewutils.misc import ConfirmView, MenuView, pagify, STAFFSERVER, get_file_name
import datetime


def round_speed(speed):
    try:
        s = f"{speed:.0f}"
    except:
        s = "?"
    return s


def round_stat(stat):
    return "?" if stat == "?" else round(stat)


class MewBotAdmin(commands.Cog):
    def parse_params(self, params: dict):
        msg = ""
        for parameter in params.keys():
            msg += f"<{parameter}> "
        return msg

    @commands.hybrid_group()
    @discord.app_commands.guilds(STAFFSERVER)
    async def admin(self, ctx):
        ...

    @admin.command(name="help")
    @discord.app_commands.guilds(STAFFSERVER)
    async def _help_message(self, ctx):
        """Staff Help Maybe"""
        embed = discord.Embed()
        desc = ""
        for command in ctx.cog.walk_commands():
            if isinstance(command, commands.HybridGroup):
                continue
            desc += f"`/{command.qualified_name} {self.parse_params(command.clean_params)}` - {command.short_doc}\n"
        kitty_cat_cog = ctx.bot.get_cog("KittyCat")
        for command in kitty_cat_cog.walk_commands():
            if (isinstance(command, commands.HybridGroup)) or (
                str(command.root_parent) == "owner"
            ):
                continue
            desc += f"`/{command.qualified_name} {self.parse_params(command.clean_params)}` - {command.short_doc}\n"
        pages = pagify(desc, per_page=20, base_embed=embed)
        await MenuView(ctx, pages).start()

    @check_admin()
    @discord.app_commands.describe(extension_name="The name of the extension to load.")
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def load(self, ctx, extension_name: str):
        """Loads an extension."""
        if "mew.cogs" in extension_name:
            extension_name = extension_name.replace("mew.cogs", "mewcogs")
        if not extension_name.startswith("mewcogs."):
            extension_name = f"mewcogs.{extension_name}"

        launcher_res = await ctx.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return await ctx.send(
                f"Launcher did not respond.  Please start with the launcher to use this command across all clusters.  If attempting to reload on this cluster alone, please use `{ctx.prefix}loadsingle {extension_name}`"
            )

        processes = len(launcher_res[0])
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
            e.description = f"Failed to load package on all clusters:\n`{load_res[0]['cogs'][extension_name]['message']}`"
        else:
            for cluster in load_res:
                if cluster["cogs"][extension_name]["success"]:
                    builder += (
                        f"`Cluster #{cluster['cluster_id']}`: Successfully loaded\n"
                    )
                else:
                    msg = cluster["cogs"][extension_name]["message"]
                    builder += f"`Cluster #{cluster['cluster_id']}`: {msg}\n"
            e.description = builder

        class FSnow:
            def __init__(self, id):
                self.id = id

        await ctx.send("Syncing Commands...")
        await ctx.bot.tree.sync()
        await ctx.bot.tree.sync(guild=FSnow(STAFFSERVER))
        await ctx.send("Successfully Synced.")
        await ctx.send(embed=e)

    @check_mod()
    @discord.app_commands.describe(
        extension_name="The name of the extension to reload."
    )
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def reload(self, ctx, extension_name: str):
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
        await ctx.bot.tree.sync()
        await ctx.bot.tree.sync(guild=FSnow(STAFFSERVER))
        await ctx.send("Successfully Synced.")
        await ctx.send(embed=e)

    @check_admin()
    @discord.app_commands.describe(extension_name="The name of the extension to unoad.")
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def unload(self, ctx, extension_name: str):
        """Unloads an extension."""
        if "mew.cogs" in extension_name:
            extension_name = extension_name.replace("mew.cogs", "mewcogs")
        if not extension_name.startswith("mewcogs."):
            extension_name = f"mewcogs.{extension_name}"

        launcher_res = await ctx.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return await ctx.send(
                f"Launcher did not respond.  Please start with the launcher to use this command across all clusters.  If attempting to reload on this cluster alone, please use `{ctx.prefix}unloadsingle {extension_name}`"
            )

        processes = len(launcher_res[0])
        unload_res = await ctx.bot.handler(
            "unload", processes, args={"cogs": [extension_name]}, scope="bot"
        )
        unload_res.sort(key=lambda x: x["cluster_id"])

        e = discord.Embed(color=0xFFB6C1)
        builder = ""
        message_same = (
            all(
                [
                    unload_res[0]["cogs"][extension_name]["message"]
                    == nc["cogs"][extension_name]["message"]
                    for nc in unload_res
                ]
            )
            and unload_res[0]["cogs"][extension_name]["message"]
        )
        if message_same:
            e.description = f"Failed to unload package on all clusters:\n`{unload_res[0]['cogs'][extension_name]['message']}`"
        else:
            for cluster in unload_res:
                if cluster["cogs"][extension_name]["success"]:
                    builder += (
                        f"`Cluster #{cluster['cluster_id']}`: Successfully unloaded\n"
                    )
                else:
                    msg = cluster["cogs"][extension_name]["message"]
                    builder += f"`Cluster #{cluster['cluster_id']}`: {msg}\n"
            e.description = builder
        await ctx.send(embed=e)

    # @check_admin()
    # @admin.command()
    # async def reloadsingle(self, ctx, extension_name: str):
    #     """Dafuq is this?"""
    #     if "mew.cogs" in extension_name:
    #         extension_name = extension_name.replace("mew.cogs", "mewcogs")
    #     if not extension_name.startswith("mewcogs."):
    #         extension_name = f"mewcogs.{extension_name}"
    #     try:
    #         ctx.bot.unload_extension(extension_name)
    #     except:
    #         # eh
    #         pass

    #     try:
    #         ctx.bot.load_extension(extension_name)
    #     except Exception as e:
    #         await ctx.send(f"Failed to reload package: `{type(e).__name__}: {str(e)}`")
    #         return

    #     await ctx.send(f"you should be running from the launcher :p\n\nSuccessfully reloaded {extension_name}.")

    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def cogs(self, ctx):
        """View the currently loaded cogs."""
        cogs = sorted([x.replace("mewcogs.", "") for x in ctx.bot.extensions.keys()])
        embed = discord.Embed(
            title=f"{len(cogs)} loaded:", description=", ".join(cogs), color=0xFF69B4
        )
        await ctx.send(embed=embed)

    @check_mod()
    @discord.app_commands.describe(user="The user ID to reset tradelock.")
    @admin.command(aliases=["resettradelock", "deltradelock"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def detradelock(self, ctx, user_id):
        """Reset the redis market tradelock for a user"""
        result = await ctx.bot.redis_manager.redis.execute(
            "LREM", "tradelock", "1", user_id
        )
        if result == 0:
            await ctx.send(
                "That user was not in the Redis tradelock.  Are you sure you have the right user?"
            )
        else:
            await ctx.send("Successfully removed the user from the Redis tradelock.")

    @check_investigator()
    @discord.app_commands.describe(id="The user ID to trade ban.")
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def tradeban(self, ctx, id):  # Looks like tradelock is temporary?
        """Permanently trade-ban a user"""
        id = int(id)
        async with ctx.bot.db[0].acquire() as pconn:
            is_tradebanned = await pconn.fetchval(
                "SELECT tradelock FROM users WHERE u_id = $1", id
            )
            if is_tradebanned is None:
                await ctx.send("User has not started, cannot trade ban.")
                return
            if is_tradebanned:
                await ctx.send("User already trade banned.")
                return
            await pconn.execute(
                "UPDATE users SET tradelock = $1 WHERE u_id = $2", True, id
            )
        await ctx.send(f"Successfully trade banned USER ID - {id}")

    @check_mod()
    @discord.app_commands.describe(id="The user ID to reset tradeban.")
    @admin.command(aliases=["untradeban", "deltradeban"])
    @discord.app_commands.guilds(STAFFSERVER)
    async def detradeban(self, ctx, id):
        """Resets a Users' tradeban"""
        id = int(id)
        async with ctx.bot.db[0].acquire() as pconn:
            is_tradebanned = await pconn.fetchval(
                "SELECT tradelock FROM users WHERE u_id = $1", id
            )
            if is_tradebanned is None:
                await ctx.send("User has not started, cannot remove trade ban.")
                return
            if not is_tradebanned:
                await ctx.send("User is not trade banned.")
                return
            await pconn.execute(
                "UPDATE users SET tradelock = $1 WHERE u_id = $2", False, id
            )
        await ctx.send(f"Successfully removed trade ban from USER ID - {id}")
        
        
    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def create_image(self, ctx, name: str, shiny: bool, *, skin: str = None, image_url: str):
        # Check if the URL is valid
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(image_url) as response:
                    if response.status != 200:
                        await ctx.send("Invalid image URL. Please provide a valid URL.")
                        return
            except Exception as e:
                await ctx.send(f"An error occurred while checking the image URL: {e}")
                return

        # Define the destination folder
        destination_folder = '/home/dyroot/mewbot/shared/duel/sprites/'

        # Create a new filename based on the parameters
        # filename = f"{name}_{skin}_{'shiny' if shiny else 'normal'}.png"
        try:
            filename = await get_file_name(name, ctx.bot, shiny = shiny, skin = skin)
        except:
            await ctx.send(f"Invalid name ({name}) passed to mew/utils/misc.py get_file_name.")

        # Build the full destination path
        full_destination_path = os.path.join(destination_folder, filename)

        # Download and save the image
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        with open(full_destination_path, 'wb') as f:
                            f.write(await response.read())
                        await ctx.send(f"Image '{filename}' has been successfully created and stored.")
                    else:
                        await ctx.send(f"Failed to download the image: HTTP status {response.status}")
        except Exception as e:
            await ctx.send(f"An error occurred while downloading and saving the image: {e}")

        
    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def forcelearn(
        self,
        ctx,
        *,
        global_id: int,
        slot: Literal[1, 2, 3, 4],
        new_move: str
    ):
        """Force a move on a Pokemon"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET moves[$1] = $2 WHERE id = $3",
                slot,
                new_move.lower().replace(' ', '-'),
                global_id
            )
            await ctx.send(":white_check_mark:")
    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def createpoke(
        self,
        ctx,
        *,
        pokemon: str,
        shiny: bool,
        skin: str,
        boosted: bool,
        u_id: str
    ):
        """Creates a new poke and gives it to the author."""
        extras = ""
        if shiny:
            extras += "shiny "
        if boosted:
            extras += "boosted "
        if skin == "false":
            skin = None
        if u_id is None:
            u_id = ctx.author.id
        else:
            u_id = int(u_id)
        pokemon = pokemon.replace(" ", "-").capitalize()
        if skin == 'none':
            pokedata = await ctx.bot.commondb.create_poke(
                ctx.bot, u_id, pokemon, shiny=shiny, boosted=boosted
            )
        else:
            pokedata = await ctx.bot.commondb.create_poke(
                ctx.bot, u_id, pokemon, shiny=shiny, skin=skin, boosted=boosted
            )
        ivpercent = round((pokedata.iv_sum / 186) * 100, 2)
        await ctx.send(f"Gave you a {extras}{pokemon} w/iv {ivpercent}%!")

    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    @discord.app_commands.describe(skin="Leave Blank for no skin")
    async def set_skin(self, ctx, globalid: int, skin: str = None):
        """ADMIN: Add a skin to pokemon via its globalid"""
        if not skin:
            await ctx.send("Will remove the Skin of the Pokemon...")
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET skin = $1 WHERE id = $2",
                skin,
                globalid,
            )
        await ctx.send(
            "Successfully added skin to pokemon"
            if skin
            else "Removed Skin from Pokemon"
        )

    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def add_skin(self, ctx, user: discord.Member, pokname: str, skinname: str):
        """ADMIN: Add a skin to a users' skin inventory"""
        pokname = pokname.lower()
        skinname = skinname.lower()
        async with ctx.bot.db[0].acquire() as pconn:
            skins = await pconn.fetchval(
                "SELECT skins::json FROM users WHERE u_id = $1", user.id
            )
            if pokname not in skins:
                skins[pokname] = {}
            if skinname not in skins[pokname]:
                skins[pokname][skinname] = 1
            else:
                skins[pokname][skinname] += 1
            await pconn.execute(
                "UPDATE users SET skins = $1::json WHERE u_id = $2", skins, user.id
            )
        await ctx.send(f"Gave `{user}` a `{skinname}` skin for `{pokname}`.")

    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def set_ot(self, ctx, pokeid: int, user: discord.Member):
        """ADMIN: Set pokes OT"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET caught_by = $1 where id = $2", user.id, pokeid
            )
            await ctx.send(f"```Elm\n- Successflly set OT of `{pokeid}` to {user}```")

    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def editiv(
        self,
        ctx,
        essence: Literal["False", "True"],
        iv: Literal["hpiv", "atkiv", "defiv", "spatkiv", "spdefiv", "speediv"],
        amount: int,
        globalid: int,
    ):
        if not iv in ["hpiv", "atkiv", "defiv", "spatkiv", "spdefiv", "speediv"]:
            return
        async with ctx.bot.db[0].acquire() as pconn:
            if essence == "True":
                await pconn.execute(
                    f"UPDATE pokes SET {iv} = $1, crystalized = True WHERE id = $2",
                    amount,
                    globalid,
                )
            else:
                await pconn.execute(
                    f"UPDATE pokes set {iv} = $1 WHERE id = $2", amount, globalid
                )
            await ctx.send(":white_check_mark:")

    @check_admin()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def edit_essence(self, ctx, user: discord.User, x_y: str = None):
        if x_y:
            x_y = [int(i) for i in x_y.split()]
        else:
            x_y = [0, 0]
        print(x_y)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                f"UPDATE users set essence = $1 WHERE u_id = $2", x_y, user.id
            )
            await ctx.send(":white_check_mark:")

    @commands.hybrid_group()
    async def gym(self, ctx):
        ...

    @check_gymauth()
    @gym.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def reward(self, ctx, mewcoins: int, user: str):
        """GYM-AUTH: Gym mewcoins Reward"""
        user = int(user)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                mewcoins,
                user,
            )
        await ctx.bot.get_partial_messageable(998316464719278280).send(
            f"{ctx.author}: <@{user}> has been awarded {mewcoins} for a gym challenge."
        )
        await ctx.send(f"<@{user}> has been awarded {mewcoins} for a gym challenge.\n")

    @check_gymauth()
    @commands.hybrid_command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def tradable(self, ctx, pokeid: int, answer: bool):
        """MOD: Set pokemon trade-able or not"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET tradable = $1 WHERE id = $2",
                answer,
                pokeid,
            )
        await ctx.send(f"Successfully set trade-able to {answer}")

    @commands.hybrid_group(aliases=["tradelogs", "tl"])
    async def tradelog(self, ctx):
        """INVESTIGATOR: Tradelog command"""
        pass

    @check_investigator()
    @tradelog.command(name="user")
    @discord.app_commands.guilds(STAFFSERVER)
    async def tradelog_user(self, ctx, u_id: str):
        u_id = int(u_id)
        async with ctx.bot.db[0].acquire() as pconn:
            trade_sender = await pconn.fetch(
                "SELECT * FROM trade_logs WHERE $1 = sender ORDER BY t_id ASC", u_id
            )
            trade_receiver = await pconn.fetch(
                "SELECT * FROM trade_logs WHERE $1 = receiver ORDER BY t_id ASC", u_id
            )
        # List[Tuple] -> (T_ID, Optional[DateTime], Traded With, Sent Creds, Sent Redeems, # Sent Pokes, Rec Creds, Rec Redeems, # Rec Pokes)
        trade = []
        t_s = trade_sender.pop(0) if trade_sender else None
        t_r = trade_receiver.pop(0) if trade_receiver else None
        while t_s or t_r:
            if t_s is None:
                trade.append(
                    (
                        t_r["t_id"],
                        t_r["time"],
                        t_r["sender"],
                        t_r["receiver_credits"],
                        t_r["receiver_redeems"],
                        len(t_r["receiver_pokes"]),
                        t_r["sender_credits"],
                        t_r["sender_redeems"],
                        len(t_r["sender_pokes"]),
                    )
                )
                t_r = trade_receiver.pop(0) if trade_receiver else None
            elif t_r is None:
                trade.append(
                    (
                        t_s["t_id"],
                        t_s["time"],
                        t_s["receiver"],
                        t_s["sender_credits"],
                        t_s["sender_redeems"],
                        len(t_s["sender_pokes"]),
                        t_s["receiver_credits"],
                        t_s["receiver_redeems"],
                        len(t_s["receiver_pokes"]),
                    )
                )
                t_s = trade_sender.pop(0) if trade_sender else None
            elif t_s["t_id"] > t_r["t_id"]:
                trade.append(
                    (
                        t_r["t_id"],
                        t_r["time"],
                        t_r["sender"],
                        t_r["receiver_credits"],
                        t_r["receiver_redeems"],
                        len(t_r["receiver_pokes"]),
                        t_r["sender_credits"],
                        t_r["sender_redeems"],
                        len(t_r["sender_pokes"]),
                    )
                )
                t_r = trade_receiver.pop(0) if trade_receiver else None
            else:
                trade.append(
                    (
                        t_s["t_id"],
                        t_s["time"],
                        t_s["receiver"],
                        t_s["sender_credits"],
                        t_s["sender_redeems"],
                        len(t_s["sender_pokes"]),
                        t_s["receiver_credits"],
                        t_s["receiver_redeems"],
                        len(t_s["receiver_pokes"]),
                    )
                )
                t_s = trade_sender.pop(0) if trade_sender else None

        if not trade:
            await ctx.send("That user has not traded!")
            return

        raw = ""
        now = datetime.datetime.now(datetime.timezone.utc)
        name_map = {}
        for t in trade:
            if t[1] is None:
                time = "?"
            else:
                d = t[1]
                d = now - d
                if d.days:
                    time = str(d.days) + "d"
                elif d.seconds // 3600:
                    time = str(d.seconds // 3600) + "h"
                elif d.seconds // 60:
                    time = str(d.seconds // 60) + "m"
                elif d.seconds:
                    time = str(d.seconds) + "s"
                else:
                    time = "?"
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
                embed = discord.Embed(
                    title=f"Trade history of user {u_id}",
                    description=page,
                    color=0xDD00DD,
                )
                embed.set_footer(text=f"Page {(idx // PER_PAGE) + 1}/{total_pages}")
                pages.append(embed)
                page = ""

        await MenuView(ctx, pages).start()

    @check_investigator()
    @tradelog.command(name="poke")
    @discord.app_commands.guilds(STAFFSERVER)
    async def tradelog_poke(self, ctx, p_id: int):
        async with ctx.bot.db[0].acquire() as pconn:
            trade_sender = await pconn.fetch(
                "SELECT * FROM trade_logs WHERE $1 = any(sender_pokes) ORDER BY t_id ASC",
                p_id,
            )
            trade_receiver = await pconn.fetch(
                "SELECT * FROM trade_logs WHERE $1 = any(receiver_pokes) ORDER BY t_id ASC",
                p_id,
            )
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
                time = "?"
            else:
                d = t[1]
                d = now - d
                if d.days:
                    time = str(d.days) + "d"
                elif d.seconds // 3600:
                    time = str(d.seconds // 3600) + "h"
                elif d.seconds // 60:
                    time = str(d.seconds // 60) + "m"
                elif d.seconds:
                    time = str(d.seconds) + "s"
                else:
                    time = "?"
            raw += f"**{t[0]}**: {t[2]} -> {t[3]} ({time} ago)\n"

        PER_PAGE = 15
        page = ""
        pages = []
        raw = raw.strip().split("\n")
        total_pages = ((len(raw) - 1) // PER_PAGE) + 1
        for idx, part in enumerate(raw):
            page += part + "\n"
            if idx % PER_PAGE == PER_PAGE - 1 or idx == len(raw) - 1:
                embed = discord.Embed(
                    title=f"Trade history of poke {p_id}",
                    description=page,
                    color=0xDD00DD,
                )
                embed.set_footer(text=f"Page {(idx // PER_PAGE) + 1}/{total_pages}")
                pages.append(embed)
                page = ""

        await MenuView(ctx, pages).start()

    @check_investigator()
    @tradelog.command(name="info")
    @discord.app_commands.guilds(STAFFSERVER)
    async def tradelog_info(self, ctx, t_id: int):
        """Get information on a specific trade by transaction id."""
        async with ctx.bot.db[0].acquire() as pconn:
            trade = await pconn.fetchrow(
                "SELECT * FROM trade_logs WHERE t_id = $1", t_id
            )
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
        if (
            trade["receiver_credits"]
            or trade["receiver_pokes"]
            or trade["receiver_redeems"]
        ):
            desc += f"**{trade['sender']} received:**\n"
            if trade["receiver_credits"]:
                desc += f"__Credits:__ {trade['receiver_credits']}\n"
            if trade["receiver_redeems"]:
                desc += f"__Redeems:__ {trade['receiver_redeems']}\n"
            if trade["receiver_pokes"]:
                desc += f"__Pokes:__ {trade['receiver_pokes']}\n"
        embed = discord.Embed(
            title=f"Trade ID {t_id}", description=desc, color=0xDD00DD
        )
        if trade["time"] is not None:
            embed.set_footer(text=trade["time"].isoformat(" "))
        await ctx.send(embed=embed)

    # @check_helper()
    # @commands.hybrid_command(enabled=False)
    # async def lb(self, ctx, val, num: int = None):
    #     official_admin_role = ctx.bot.official_server.get_role(519470089318301696)
    #     admins = [member.id for member in official_admin_role.members]

    #     official_mod_role = ctx.bot.official_server.get_role(519468261780357141)
    #     mods = [member.id for member in official_mod_role.members]

    #     if num == 1:
    #         num = 25
    #         snum = 0

    #     elif num is None:
    #         num = 25
    #         snum = 0

    #     else:
    #         num = num * 25
    #         snum = num - 25

    #     if val is None:
    #         em = discord.Embed(title="Leaderboard options", color=0xFFBC61)
    #         em.add_field(
    #             name="Redeems",
    #             value=f"`{ctx.prefix}leaderboard redeems` for redeems leaderboard",
    #         )
    #         await ctx.send(embed=em)
    #     elif val.lower() in ("creds", "credits"):
    #         index_num = 0
    #         async with ctx.bot.db[0].acquire() as pconn:
    #             leaders = await pconn.fetch(
    #                 f"SELECT tnick, mewcoins, u_id, staff FROM users ORDER BY mewcoins DESC LIMIT {num}"
    #             )
    #         nicks = [record["tnick"] for record in leaders]
    #         coins = [record["mewcoins"] for record in leaders]
    #         ids = [record["u_id"] for record in leaders]
    #         staffs = [record["staff"] for record in leaders]
    #         embed = discord.Embed(title="Credit Rankings!", color=0xFFB6C1)
    #         desc = ""
    #         for idx, coin in enumerate(coins[snum:num], start=snum):
    #             id = ids[idx]
    #             is_staff = staffs[idx] != "User"
    #             #if (id in mods) or (id in admins) or (is_staff):
    #             #    continue
    #             nick = nicks[idx]
    #             try:
    #                 name = (await ctx.bot.fetch_user(id)).name
    #             except:
    #                 name = "Unknown User"
    #             index_num += 1
    #             desc += f"__{index_num}__. {coin:,.0f} Credits - {name}\n"
    #             # {coins} Credits {coins} Credits
    #         embed.description = desc
    #         await ctx.send(embed=embed)
    #     elif val.lower() in ("redeems", "redeem", "deems"):
    #         index_num = 0
    #         async with ctx.bot.db[0].acquire() as pconn:
    #             leaders = await pconn.fetch(
    #                 f"SELECT tnick, redeems, u_id FROM users ORDER BY redeems DESC LIMIT {num}"
    #             )
    #         nicks = [record["tnick"] for record in leaders]
    #         coins = [record["redeems"] for record in leaders]
    #         ids = [record["u_id"] for record in leaders]
    #         embed = discord.Embed(title="Redeem Rankings!", color=0xFFB6C1)
    #         desc = ""
    #         for idx, id in enumerate(ids[snum:num], start=snum):
    #             if id in mods or id in admins:
    #                 continue
    #             coin = coins[idx]
    #             nick = nicks[idx]
    #             name = ctx.bot.get_user(id)
    #             index_num += 1
    #             desc += f"__{index_num}__. {name.name} - {coin:,.0f} Redeems\n"
    #         embed.description = desc
    #         await ctx.send(embed=embed)
    #     else:
    #         await ctx.send("Choose Redeems, and thats it! Just redeems!")

    @check_mod()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def combine(self, ctx, user1: str, user2: str):
        """ADMIN: Add two users pokes together, leaving user1 with all, and user2 with none."""
        u_id1, u_id2 = int(user1), int(user2)
        # def check(m):
        #     return m.author.id == ctx.author.id and m.content.lower() in (
        #         "yes",
        #         "no",
        #         "y",
        #         "n",
        #     )
        # try:
        #     m = await ctx.bot.wait_for("message", check=check, timeout=30)
        # except asyncio.TimeoutError:
        #     await ctx.send("Request timed out.")
        #     return
        yes = Button(style=discord.ButtonStyle.green, label="Yes")
        no = Button(style=discord.ButtonStyle.red, label="No")

        async def no_click(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content=f"Canceled", embed=None, view=None
            )
            return

        async def yes_click(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content=f"Combining Pokemon...", embed=None, view=None
            )
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
            await ctx.send(
                f"```elm\nSuccessfully added pokemon from {u_id2} to {u_id1}.```"
            )

        yes.callback = yes_click
        no.callback = no_click
        view = View()
        view.add_item(item=yes)
        view.add_item(item=no)
        await ctx.send(
            f"Are you sure you want to move all pokemon from {u_id2} to {u_id1}?",
            view=view,
        )

    @check_mod()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def getuser(self, ctx, user):
        """MOD: Get user info by ID"""
        user = int(user)
        async with ctx.bot.db[0].acquire() as pconn:
            info = await pconn.fetchrow("SELECT * FROM users WHERE u_id = $1", user)
            bound_data = await pconn.fetchrow(
                "SELECT * FROM account_bound WHERE u_id = $1", user
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
        desc = f"**__Information on {user}__**"
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
        embed.add_field(name=f"Bound Data", value=f"{bound_data}", inline=False)
        embed.set_footer(text="Information live from Database")
        await ctx.send(embed=embed)

    @check_mod()
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    @discord.app_commands.describe(
        command="The command to mock, prefix must not be entered."
    )
    async def mock(self, ctx, user_id, *, command):
        """MOD:
        Mock another user invoking a command.
        """
        user_id = int(user_id)
        raw = command
        user = ctx.bot.get_user(user_id)
        if not user:
            try:
                user = await ctx.bot.fetch_user(user_id)
            except discord.HTTPException:
                await ctx.send("User not found.")
                return
        ctx.author = user

        class FakeInteraction:
            pass

        ctx._interaction = FakeInteraction()
        ctx._interaction.id = ctx.message.id

        path = ""
        command = None
        args = ""
        # This is probably not super efficient, but I don't care to optimize
        # dev-facing code super hard...
        for part in raw.split(" "):
            if command:
                args += part + " "
            else:
                path += part + " "
                command = ctx.bot.get_command(path)
                if isinstance(command, commands.hybrid.HybridGroup):
                    command = None
        if command is None:
            await ctx.send("I can't find a command that matches that input.")
            return
        # Just... trust me, this gets a list of type objects for the command's args
        signature = [
            x.annotation
            for x in inspect.signature(command.callback).parameters.values()
        ][2:]
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

    @check_helper()
    @discord.app_commands.describe(shards_of_cluster="The user ID to reset tradelock.")
    @admin.command()
    @discord.app_commands.guilds(STAFFSERVER)
    async def shards(self, ctx, shards_of_cluster: int = None):
        """View information of all shards across the bot."""
        if shards_of_cluster is None:
            shards_of_cluster = ctx.bot.cluster["id"]
        process_res = await ctx.bot.handler(
            "send_shard_info", 1, args={"cluster_id": shards_of_cluster}, scope="bot"
        )
        if not len(process_res):
            await ctx.send("Cluster is dead or does not exist.")
            return

        process_res = process_res[0]

        shard_groups = process_res["shards"]
        cluster_id = process_res["id"]
        cluster_name = process_res["name"]

        pages = []
        current = discord.Embed(
            title=f"Cluster #{cluster_id} ({cluster_name})",
            color=0xFFB6C1,
        )
        current.set_footer(text=f"{ctx.prefix}[ n|next, b|back, s|start, e|end ]")
        for s in shard_groups.values():
            msg = (
                "```prolog\n"
                f"Latency:   {s['latency']}ms\n"
                f"Guilds:    {s['guilds']}\n"
                f"Channels:  {s['channels']}\n"
                f"Users:     {s['users']}\n"
                "```"
            )
            current.add_field(
                name=f"Shard `{s['id']}/{ctx.bot.shard_count}`", value=msg
            )

        pages.append(current)

        embed = await ctx.send(embed=pages[0])
        current_page = 1

        def get_value(message):
            return {
                f"{ctx.prefix}n": min(len(pages) - 1, current_page + 1),
                f"{ctx.prefix}next": min(len(pages) - 1, current_page + 1),
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


async def setup(bot):
    await bot.add_cog(MewBotAdmin())
