import discord
from discord.ext import commands
from discord import Embed

from mewcogs.pokemon_list import *
from mewcogs.json_files import *
from mewcogs.market import (
    PATREON_SLOT_BONUS,
    YELLOW_PATREON_SLOT_BONUS,
    SILVER_PATREON_SLOT_BONUS,
    CRYSTAL_PATREON_SLOT_BONUS,
)
from mewutils.misc import get_pokemon_image, pagify, MenuView, ConfirmView
from mewutils.checks import tradelock
from pokemon_utils.utils import evolve
from typing import Literal
import aiohttp
import asyncio
import cpuinfo
import os
import psutil
import random
import subprocess
import time
import ujson
from math import floor
from datetime import datetime, timedelta
import re
import ast


def do_health(maxHealth, health, healthDashes=10):
    dashConvert = int(
        maxHealth / healthDashes
    )  # Get the number to divide by to convert health to dashes (being 10)
    currentDashes = int(
        health / dashConvert
    )  # Convert health to dash count: 80/10 => 8 dashes
    remainingHealth = (
        healthDashes - currentDashes
    )  # Get the health remaining to fill as space => 12 spaces
    cur = f"{round(health)}/{maxHealth}"

    healthDisplay = "".join(
        ["▰" for i in range(currentDashes)]
    )  # Convert 8 to 8 dashes as a string:   "--------"
    remainingDisplay = "".join(
        ["▱" for i in range(remainingHealth)]
    )  # Convert 12 to 12 spaces as a string: "            "
    percent = floor(
        (health / maxHealth) * 100
    )  # Get the percent as a whole number:   40%
    if percent < 1:
        percent = 0
    return f"{healthDisplay}{remainingDisplay}\n           {cur}"  # Print out textbased healthbar


def calculate_breeding_multiplier(level):
    difference = 0.02
    return f"{round((1 + (level) * difference), 2)}x"


def calculate_iv_multiplier(level):
    difference = 0.5
    return f"{round((level * difference), 1)}%"


class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize())

    async def initialize(self):
        # This is to make sure the dict exists before we access in the cog check
        await self.bot.redis_manager.redis.execute(
            "HMSET", "resetcooldown", "examplekey", "examplevalue"
        )

    @commands.hybrid_group()
    async def spread(self, ctx):
        ...

    @spread.command()
    async def honey(self, ctx):
        """Spread honey in this channel to attract Pokémon."""
        async with ctx.bot.db[0].acquire() as pconn:
            user_honey = await pconn.fetchval(
                "SELECT honey FROM account_bound WHERE u_id = $1", 
                ctx.author.id
            )
            if user_honey is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            honey = await pconn.fetchval(
                "SELECT * FROM honey WHERE channel = $1 LIMIT 1",
                ctx.channel.id,
            )
            if honey is not None:
                await ctx.send(
                    "There is already honey in this channel! You can't add more yet."
                )
                return
            if user_honey >= 1:
                await self.bot.commondb.remove_bag_item(
                    ctx.author.id,
                    "honey",
                    1,
                    True
                )
            else:
                await ctx.send("You do not have any units of Honey!")
                return
            expires = int(time.time() + (60 * 60))
            await pconn.execute(
                "INSERT INTO honey (channel, expires, owner, type) VALUES ($1, $2, $3, 'honey')",
                ctx.channel.id,
                expires,
                ctx.author.id,
            )
            await ctx.send(
                f"You have successfully spread some of your honey, rare spawn chance increased by nearly 20 times normal in this channel for the next hour!"
            )

    @commands.hybrid_command()
    async def leaderboard(
        self, ctx, board: Literal["Votes", "Servers", "Pokemon", "Fishing", "Mining"]
    ):
        """Displays a Leaderboard Based on Votes, Servers, Pokémon or Fishing."""
        LEADERBOARD_IMMUNE_USERS = [
            195938951188578304,  # gomp
            3746,  # not a real user, just used to store pokes and such
        ]
        if board.lower() == "vote":
            async with ctx.bot.db[0].acquire() as pconn:
                leaders = await pconn.fetch(
                    "SELECT tnick, vote_streak, u_id, staff FROM users WHERE last_vote >= $1 ORDER BY vote_streak DESC",
                    time.time() - (36 * 60 * 60),
                )
            names = [record["tnick"] for record in leaders]
            votes = [record["vote_streak"] for record in leaders]
            ids = [record["u_id"] for record in leaders]
            staffs = [record["staff"] for record in leaders]
            embed = discord.Embed(title="Upvote Streak Rankings!", color=0xFFB6C1)
            desc = ""
            true_idx = 1
            for idx, vote in enumerate(votes):
                if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                    continue
                if names[idx] is not None:
                    name = f"{names[idx]} - ({ids[idx]})"
                else:
                    name = f"Unknown user - ({ids[idx]})"
                desc += f"{true_idx}. {vote:,} votes - {name}\n"
                true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        elif board.lower() == "servers":
            total = []
            launcher_res = await self.bot.handler("statuses", 1, scope="launcher")
            if not launcher_res:
                await ctx.send(
                    "I can't process that request right now, try again later."
                )
                return
            processes = len(launcher_res[0])
            body = "return {x.name: x.member_count for x in bot.guilds if x.member_count is not None}"
            eval_res = await self.bot.handler(
                "_eval",
                processes,
                args={"body": body, "cluster_id": "-1"},
                scope="bot",
                _timeout=5,
            )
            if not eval_res:
                await ctx.send(
                    "I can't process that request right now, try again later."
                )
                return
            for response in eval_res:
                if response["message"]:
                    total.extend(ast.literal_eval(response["message"]).items())
            total.sort(key=lambda a: a[1], reverse=True)
            embed = discord.Embed(title="Top Servers with Mewbot!", color=0xFFB6C1)
            desc = ""
            true_idx = 1
            for idx, data in enumerate(total):
                name, count = data
                desc += f"{true_idx}. {count:,} members - {name}\n"
                true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        elif board.lower() == "pokemon":
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetch(
                    """SELECT u_id, cardinality(pokes) as pokenum, staff, tnick FROM users ORDER BY pokenum DESC"""
                )
            pokes = [record["pokenum"] for record in details]
            ids = [record["u_id"] for record in details]
            staffs = [record["staff"] for record in details]
            names = [record["tnick"] for record in details]
            embed = discord.Embed(title="Pokemon Leaderboard!", color=0xFFB6C1)
            desc = ""
            true_idx = 1
            for idx, id in enumerate(ids):
                if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                    continue
                pokenum = pokes[idx]
                if names[idx] is not None:
                    name = f"{names[idx]} - ({id})"
                else:
                    name = f"Unknown user - ({id})"
                desc += f"__{true_idx}__. {pokenum:,} Pokemon - {name}\n"
                true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        elif board.lower() == "fishing":
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetch(
                    f"""SELECT u_id, fishing_points, fishing_level as pokenum, staff, tnick FROM users WHERE fishing_points != 0 ORDER BY fishing_points DESC"""
                )
            pokes = [record["pokenum"] for record in details]
            exps = [t["fishing_points"] for t in details]
            ids = [record["u_id"] for record in details]
            staffs = [record["staff"] for record in details]
            names = [record["tnick"] for record in details]
            embed = discord.Embed(
                title="Fishing Points Leaderboard",
                description="Catch some fish!",
                color=0xFFB6C1
            )
            embed.set_footer(
                text="This only accounts for users with at least 1 Fishing Point"
            )
            desc = ""
            true_idx = 1
            for idx, id in enumerate(ids):
                if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                    continue
                pokenum = pokes[idx]
                exp = exps[idx]
                if names[idx] is not None:
                    name = f"{names[idx]} - ({id})"
                else:
                    name = f"Unknown user - ({id})"
                desc += f"__{true_idx}__. `Points` : **{exp}** - `{name}`\n"
                true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        elif board.lower() == "mining":
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetch(
                    f"""SELECT u_id, mining_points, mining_level as pokenum, staff, tnick FROM users WHERE mining_points != 0 ORDER BY mining_points DESC"""
                )
            pokes = [record["pokenum"] for record in details]
            exps = [t["mining_points"] for t in details]
            ids = [record["u_id"] for record in details]
            staffs = [record["staff"] for record in details]
            names = [record["tnick"] for record in details]
            embed = discord.Embed(
                title="Mining Points Leaderboard",
                description="Mine some rocks!",
                color=0xFFB6C1
            )
            embed.set_footer(
                text="This only accounts for users with at least 1 Mining Point"
            )
            desc = ""
            true_idx = 1
            for idx, id in enumerate(ids):
                if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                    continue
                pokenum = pokes[idx]
                exp = exps[idx]
                if names[idx] is not None:
                    name = f"{names[idx]} - ({id})"
                else:
                    name = f"Unknown user - ({id})"
                desc += f"__{true_idx}__. `Points` : **{exp}** - `{name}`\n"
                true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()

    @commands.hybrid_command()
    async def server(self, ctx):
        """Display Stats of the Current Server."""
        embed = Embed(title="Server Stats", color=0xFFBC61)
        embed.add_field(
            name="Official Server",
            value="[Join the Official Server](https://discord.gg/mewbot)",
        )
        async with ctx.bot.db[0].acquire() as pconn:
            honeys = await pconn.fetch(
                "SELECT channel, expires, type FROM honey WHERE channel = ANY ($1) ",
                [channel.id for channel in ctx.guild.text_channels],
            )
        desc = ""
        for t in honeys:
            channel = t["channel"]
            expires = t["expires"]
            honey_type = t["type"]
            if honey_type == "honey":
                honey_type = "Honey"
            elif honey_type == "ghost":
                honey_type = "Ghost Detector"
            elif honey_type == "cheer":
                honey_type = "Christmas Cheer"
            # Convert the expire timestamp to 10 minute buckets of time remaining
            # Since the task that clears honey only runs every 10 minutes, it doesn't make much sense to try to be more accurate than that
            minutes = int((expires - time.time()) // 60)
            minutes -= minutes % 10
            if minutes < 0:
                minutes = "Less than 10 minutes"
            else:
                minutes = f"{minutes} minutes"
            desc += f"{honey_type} Stats for <#{channel}>\n\t**__-__Expires in {minutes}**\n"
        pages = pagify(desc, base_embed=embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_group()
    async def change(self, ctx):
        ...

    @change.command()
    @discord.app_commands.describe(nature="The nature to change to.")
    async def nature(self, ctx, nature: Literal[tuple(natlist)]):
        """
        Uses a nature capsule to change your selected Pokemon's nature.
        """
        if nature.capitalize() not in natlist:
            await ctx.send(f"That Nature does not exist!")
            return
        nature = nature.capitalize()
        async with ctx.bot.db[0].acquire() as conn:
            nature_capsule = await conn.fetchval(
                "SELECT nature_capsules FROM account_bound WHERE u_id = $1", 
                ctx.author.id
            )
            credits = await conn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1",
                ctx.author.id
            )
        if credits is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            return
        if nature_capsule is None:
            await ctx.send(f"This command uses our new bag system!\nUse `/bag convert` if you haven't!")
            return
        if nature_capsule <= 0 or nature == None:
            await ctx.send(
                "You have no nature capsules! Buy some with `/redeem nature capsules`."
            )
            return
        await self.bot.commondb.remove_bag_item(
            ctx.author.id,
            "nature_capsules",
            1,
            True
        )
        async with ctx.bot.db[0].acquire() as pconn:
            _id = await pconn.fetchval(
                "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
            )
            await pconn.execute(
                "UPDATE pokes SET nature = $1 WHERE id = $2", nature, _id
            )
        await ctx.send(
            f"You have successfully changed your selected Pokemon's nature to {nature}"
        )

    #@commands.hybrid_command()
    async def bag(self, ctx):
        """
        Lists your items in your backpack.
        """
        async with ctx.bot.db[0].acquire() as conn:
            dets = await conn.fetchval(
                "SELECT items::json FROM users WHERE u_id = $1", ctx.author.id
            )
        if dets is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            return
        desc = ""
        for item in dets:
            if dets[item] > 0:
                desc += f"{item.replace('-', ' ').capitalize()} : {dets[item]}x\n"
        if not desc:
            e = Embed(title="Your Current Bag", color=0xFFB6C1, description="Empty :(")
            await ctx.send(embed=e)
            return

        embed = Embed(title="Your Current Bag", color=0xFFB6C1)
        pages = pagify(desc, per_page=20, base_embed=embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_command()
    async def updates(self, ctx):
        """Lists recent updates."""
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetch(
                "SELECT id, dev, update, update_date FROM updates ORDER BY update_date DESC"
            )
        updates = [t["update"] for t in details]
        dates = [t["update_date"] for t in details]
        devs = [t["dev"] for t in details]
        desc = ""
        for idx, date in enumerate(dates):
            month = date.strftime("%B")
            desc += (
                f"**{month} {date.day}, {date.year} - {devs[idx]}**\n{updates[idx]}\n\n"
            )
        embed = discord.Embed(title="Recent Updates", colour=0xFFB6C1)
        pages = pagify(desc, sep="\n\n", per_page=5, base_embed=embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_command()
    async def status(self, ctx):
        """Get statistical information of the bot"""
        embed = Embed(color=0xFFB6C1, url="https://mewbot.xyz/")

        clusternum = 1
        shardnum = len(ctx.bot.shards)

        result = await ctx.bot.handler("num_processes", 1, scope="launcher")

        if result:
            clusternum = result[0]["clusters"]
            shardnum = result[0]["shards"]
            process_res = await ctx.bot.handler(
                "_eval",
                clusternum,
                args={"body": "return len(bot.guilds)", "cluster_id": "-1"},
                scope="bot",
            )
            servernum = 0
            for cluster in process_res:
                servernum += int(cluster["message"])
        else:
            clusternum = "1"
            shardnum = len(ctx.bot.shards)
            servernum = len(ctx.bot.guilds)

        embed.add_field(
            name="Statistics",
            value=(
                f"`Owner:` **Dylee.**\n"
                "`Developers:`**Dylee, Foreboding**\n"
                "`Web Developer:`\n"
                "`Dev. Helpers:`\n"
                f"`Server count:` **{servernum:,}**\n"
                f"`Shard count:` **{shardnum}**\n"
                f"`Cluster count:` **{clusternum}**\n"
                "\n"
                f"`Discord version:` **{discord.__version__}**\n"
                f"`Uptime:` **{ctx.bot.uptime}**\n"
                "*Community thank you/credits page coming soon!*\n"
            ),
        )

        # give users a link to invite thsi bot to their server
        embed.add_field(
            name="Invite",
            value="[Invite Me](https://discordapp.com/api/oauth2/authorize?client_id=519850436899897346&permissions=387136&scope=bot)",
        )
        # embed.add_field(
        #     name="Follow us on Social Media for fun events and rewards!",
        #     value="[`Reddit`](https://www.reddit.com/r/Mewbot/)\n[`Instagram`](https://www.instagram.com/mewbot_official/)\n[`Twitter`](https://twitter.com/MewbotOS)",
        # )
        embed.add_field(
            name="Official Wiki Page",
            value="[Wiki Tutorial](https://mewbot.wiki)",
        )
        view = discord.ui.View(timeout=60)

        async def check(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message(
                    content="You are not allowed to interact with this button.",
                    ephemeral=True,
                )
                return False
            return True

        view.interaction_check = check
        creditpage = discord.ui.Button(
            style=discord.ButtonStyle.gray, label="View Credits"
        )

        async def creditcallback(interaction):
            await self.credit_page(ctx)

        creditpage.callback = creditcallback
        view.add_item(creditpage)
        copyright = discord.ui.Button(
            style=discord.ButtonStyle.gray, label="View Copyright Info"
        )

        async def copyrightcallback(interaction):
            await self.copyright_page(ctx)

        copyright.callback = copyrightcallback
        view.add_item(copyright)
        await ctx.send(embed=embed, view=view)

    async def credit_page(self, ctx):
        """
        Our Contributors
        """
        desc = f"**Source Repo Credit**: [Gen 9 Preview Sprites](https://www.deviantart.com/kingofthe-x-roads)\n"
        desc += f"\n**Various Artwork/Skins:**"
        desc += f"\n\n**Gleam Artwork:**"
        desc += f"\n\n**Art Team:**"
        desc += f"\n\n***More will be added soon!***"
        embed = Embed(color=0xFFB6C1, description=desc)
        await ctx.send(embed=embed)

    async def copyright_page(self, ctx):
        """
        Copyright Information
        """
        desc = f"**Copyright Information**:\n"
        desc += f"\n**Pokémon © 2002-2022 Pokémon.**\n**© 1995-2022 Nintendo/Creatures Inc.**\n**/GAME FREAK inc. TM, ® and Pokémon character names are trademarks of Nintendo.**"
        desc += f"\n*No copyright or trademark infringement is intended in using Pokémon content within Mewbot.*"
        desc += " "
        embed = Embed(color=0xFFB6C1, description=desc)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def claim(self, ctx):
        """Claim upvote points!"""
        async with ctx.bot.db[0].acquire() as pconn:
            points = await pconn.fetchval(
                "SELECT upvotepoints FROM users WHERE u_id = $1", ctx.author.id
            )
            if points is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if points < 5:
                await ctx.send("You do not have enough Upvote Points for your rewards.")
                return
            await pconn.execute(
                "UPDATE users SET upvotepoints = upvotepoints - 5, redeems = redeems + $2, mewcoins = mewcoins + 15000 WHERE u_id = $1",
                ctx.author.id,
                random.randint(1, 3 if random.randint(1, 3) == 1 else 1),
            )
        await ctx.send("Upvote Points Claimed!")

    @commands.hybrid_command()
    async def ping(self, ctx):
        """PONG"""
        embed = Embed(color=0xFFB6C1)
        lat = ctx.bot.latency * 1000
        if lat == float("inf"):
            lat = "Infinity :("
        else:
            lat = f"{int(lat)}ms"

        shard_id = ctx.guild.shard_id
        cluster_id = ctx.bot.cluster["id"]
        cluster_name = ctx.bot.cluster["name"]

        embed.title = f"Cluster #{cluster_id} ({cluster_name})"
        embed.description = f"Shard {shard_id} - {lat}"
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def vote(self, ctx):
        """Vote for the Bot & get voting rewards."""
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT vote_streak, last_vote, upvotepoints FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            update_data = await pconn.fetchrow(
                "SELECT id, dev, update, update_date FROM updates ORDER BY id DESC LIMIT 1"
            )
            if data is None:
                vote_streak = 0
            elif data["last_vote"] < time.time() - (36 * 60 * 60):
                vote_streak = 0
            else:
                vote_streak = data["vote_streak"]
            uppoints = data['upvotepoints']
        embed = discord.Embed(
            title="Mewbot Voting!",
            description="Vote for Mewbot through one of the links below!\nYou'll receive 1 Upvote Point, 1,500 credits, and 5 Energy Bars after upvoting!",
            color=0xFFB6C1
        )
        embed.add_field(
            name="Websites",
            value=(
                "[#1 top.gg](https://top.gg/bot/519850436899897346/vote)\n"
                "[#2 DiscordBotList](https://discordbotlist.com/bots/mewbot/upvote)"
            ),
            inline=True
        )
        embed.add_field(
            name="Vote Counts",
            value=(
                f"<:upvote:1037942314691199089> **Upvote Points**: {uppoints}\n"
                f"**<:upvotestreak:1037942367929503766> Vote Streak**: {vote_streak}\n"
                f"Note: For Top.gg Only"
            ),
            inline=True
        )
        embed.add_field(
            name="Official Server",
            value=(
                "Join for support and our huge community of Mewbot users!\n"
                "[Mewbot Official](https://discord.gg/mewbot)"
            ),
            inline=True
        )
        embed.add_field(
            name="Newest Update!",
            value=f"{update_data['update']}\n{update_data['dev']} on {update_data['update_date']}",
            inline=False
        )

        await ctx.send(embed=embed)
        emoji = random.choice(emotes)
        await ctx.send(emoji)

    @commands.hybrid_command()
    async def predeem(self, ctx):
        """Claim patreon rewards."""
        date = datetime.now()
        date = f"{date.month}-{date.year}"
        async with ctx.bot.db[0].acquire() as pconn:
            if not await pconn.fetchval(
                "SELECT exists(SELECT * from users WHERE u_id = $1)", ctx.author.id
            ):
                await ctx.send("You have not started!\nStart with `/start` first!")
                return
            last = await pconn.fetchval(
                "SELECT lastdate FROM patreonstore WHERE u_id = $1", ctx.author.id
            )
        if last == date:
            await ctx.send(
                "You have already received your patreon redeems for this month... Come back later!"
            )
            return
        patreon_status = await ctx.bot.patreon_tier(ctx.author.id)
        if patreon_status is None:
            await ctx.send(
                "I do not recognize you as a patron. Please double check that your membership is still active.\n"
                "If you are currently a patron, but I don't recognize you, check the following things:\n\n"
                "**1.** If you subscribed within the last 15 minutes, the bot has not had enough time to process your patronage. "
                "Wait 15 minutes and try again. If waiting does not work, continue with the following steps.\n\n"
                "**2.** Check if you have linked your Discord account on your Patreon account. "
                "Follow this guide to make sure it is linked. "
                "<https://support.patreon.com/hc/en-us/articles/212052266-Get-my-Discord-role>\n\n"
                "**3.** Check that you subscribed to Patreon in a tier, instead of donating a custom amount. "
                "If you do not donate in a tier, the bot cannot identify what perks you are supposed to receive. "
                "Follow this guide to make sure you subscribe in a tier. "
                "It will explain how to make sure you are in a tier and explain how to subscribe to a tier with a custom amount. "
                "<https://support.patreon.com/hc/en-us/articles/360000126286-Editing-your-membership>\n\n"
                "If none of the above worked, ask a staff member for further assistance."
            )
            return
        if patreon_status == "Sapphire Tier":
            amount = 150
        elif patreon_status == "Crystal Tier":
            amount = 75
        elif patreon_status == "Silver Tier":
            amount = 30
        elif patreon_status == "Yellow Tier":
            amount = 15
        elif patreon_status == "Red Tier":
            amount = 3
        else:
            await ctx.send(
                "Uh oh, you have an invalid patreon tier! The tiers may have been modified without updating this command... Please report this bug!"
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            if last is None:
                await pconn.execute(
                    "INSERT INTO patreonstore (u_id, lastdate) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    ctx.author.id,
                    date,
                )
            else:
                await pconn.execute(
                    "UPDATE patreonstore SET lastdate = $2 WHERE u_id = $1",
                    ctx.author.id,
                    date,
                )
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $2 WHERE u_id = $1",
                ctx.author.id,
                amount,
            )
        await ctx.send(
            f"You have received **{amount}** redeems. Thank you for supporting Mewbot!"
        )

    @commands.hybrid_command()
    @discord.app_commands.describe(nick="The new nickname for your Pokemon")
    async def nick(self, ctx, nick: str = "None"):
        """Set or reset your selected pokemon's nickname."""
        if len(nick) > 150:
            await ctx.send("Nickname is too long!")
            return
        if any(
            word in nick
            for word in (
                "@here",
                "@everyone",
                "http",
                "nigger",
                "nigga",
                "gay",
                "fag",
                "kike",
                "jew",
                "faggot",
            )
        ):
            await ctx.send("Nope.")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET poknick = $1 WHERE id = (SELECT selected FROM users WHERE u_id = $2)",
                nick,
                ctx.author.id,
            )
        if nick == "None":
            await ctx.send("Successfully reset Pokemon nickname.")
            return
        await ctx.send(f"Successfully changed Pokemon nickname to {nick}.")

    #@commands.hybrid_command()
    async def stats(self, ctx):
        """Show some statistics about yourself."""
        async with ctx.bot.db[0].acquire() as tconn:
            details = await tconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", ctx.author.id
            )
            fishing_players = await tconn.fetch(
                f"SELECT u_id, fishing_points FROM users WHERE fishing_points != 0 ORDER BY fishing_points DESC"
            )
            ids = [record["u_id"] for record in fishing_players]

        if details is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            return
        embed = discord.Embed(
            title="Your Stats", 
            description="Different stats and levels from various activities!",
            color=0xFFB6C1
        )
        fishing_level = details["fishing_level"]
        fishing_exp = details["fishing_exp"]
        fishing_levelcap = details["fishing_level_cap"]
        fishing_points = details['fishing_points']
        energy = do_health(10, details["energy"])

        if ctx.author.id in ids:
            fishing_position = ids.index(ctx.author.id)
            position_msg = f"`Position`: {fishing_position + 1}"
        else:
            position_msg = "`Position`: Not Rated"

        embed.add_field(
            name="Fishing Stats 🐟",
            value=f"`Level`: {fishing_level} - `Exp`: {fishing_exp}/{fishing_levelcap}\n`Points`: {fishing_points} - {position_msg}",
        )

        embed.add_field(name="Energy", value=energy)
        embed.set_footer(text="If You have some Energy go fishing!")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @discord.app_commands.describe(pokemon="The Pokémon to Shadow Hunt.")
    async def hunt(self, ctx, pokemon: str):
        """Select a Pokémon to shadow hunt & get a shadow skin for it if you get lucky!"""
        pokemon = pokemon.capitalize()
        if not pokemon in totalList:
            await ctx.send("You have chosen an invalid Pokemon.")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT hunt, chain FROM users WHERE u_id = $1", ctx.author.id
            )
        if data is None:
            await ctx.send("You have not started!\nStart with `/start` first.")
            return
        hunt, chain = data
        if hunt == pokemon:
            await ctx.send("You are already hunting that pokemon!")
            return
        if (
            chain > 0
            and not await ConfirmView(
                ctx,
                f"Are you sure you want to abandon your hunt for **{hunt}**?\nYou will lose your streak of **{chain}**.",
            ).wait()
        ):
            return
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET hunt = $1, chain = 0 WHERE u_id = $2",
                pokemon,
                ctx.author.id,
            )
        e = discord.Embed(
            title="Shadow Hunt",
            description=f"Successfully changed shadow hunt selection to **{pokemon}**.",
            color=0xFFB6C1,
        )
        e.set_image(url=await get_pokemon_image(pokemon, ctx.bot, skin="shadow"))
        await ctx.send(embed=e)
        await ctx.bot.get_partial_messageable(999442907465523220).send(
            f"`{ctx.author.id} - {hunt} @ {chain}x -> {pokemon}`"
        )

    #@commands.hybrid_command()
    @discord.app_commands.describe(user="A User to view trainer information.")
    async def trainer(self, ctx, user: discord.User = None):
        """View your trainer card or the trainer card of another user."""
        if user is None:
            user = ctx.author
        async with ctx.bot.db[0].acquire() as tconn:
            details = await tconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", user.id
            )
            if details is None:
                await ctx.send(f"{user.name} has not started!")
                return
            if (
                not details["visible"]
                and user.id != ctx.author.id
                and ctx.author.id != ctx.bot.owner_id
            ):
                await ctx.send(
                    f"You are not permitted to see the Trainer card of {user.name}"
                )
                return
            pokes = details["pokes"]
            daycared = await tconn.fetchval(
                "SELECT count(*) FROM pokes WHERE id = ANY ($1) AND pokname = 'Egg'",
                pokes,
            )
            usedmarket = await tconn.fetchval(
                "SELECT count(id) FROM market WHERE owner = $1 AND buyer IS NULL",
                user.id,
            )

        visible = details["visible"]
        u_id = details["u_id"]
        redeems = details["redeems"]
        tnick = details["tnick"]
        uppoints = details["upvotepoints"]
        mewcoins = details["mewcoins"]
        evpoints = details["evpoints"]
        dlimit = details["daycarelimit"]
        hitem = details["held_item"]
        marketlimit = details["marketlimit"]
        dets = details["inventory"]
        count = len(pokes)
        is_staff = details["staff"]

        embed = Embed(color=0xFFB6C1)
        if is_staff.lower() != "user":
            embed.set_author(
                name=f"{tnick if tnick is not None else user.name} Trainer Card",
                icon_url="https://cdn.discordapp.com/attachments/707730610650873916/773574461474996234/logo_mew.png",
            )
        else:
            embed.set_author(
                name=f"{tnick if tnick is not None else user.name} Trainer Card"
            )
        embed.add_field(name="Redeems", value=f"{redeems:,}", inline=True)
        embed.add_field(name="Upvote Points", value=f"{uppoints}", inline=True)
        embed.add_field(
            name="Credits",
            value=f"{mewcoins:,}<:mewcoin:1010959258638094386>",
            inline=True,
        )
        embed.add_field(name="Pokemon Count", value=f"{count:,}", inline=True)
        embed.add_field(name="EV Points", value=f"{evpoints:,}", inline=True)
        embed.add_field(
            name="Daycare spaces", value=f"{daycared}/{dlimit}", inline=True
        )
        dets = ujson.loads(dets)
        dets.pop("coin-case", None) if "coin-case" in dets else None
        for item in dets:
            embed.add_field(
                name=item.replace("-", " ").capitalize(),
                value=f"{dets[item]}{'%' if 'shiny' in item or 'honey' in item else 'x'}",
                inline=True,
            )
        patreon_status = await ctx.bot.patreon_tier(user.id)
        if patreon_status in ("Crystal Tier", "Sapphire Tier"):
            marketlimitbonus = CRYSTAL_PATREON_SLOT_BONUS
        elif patreon_status == "Silver Tier":
            marketlimitbonus = SILVER_PATREON_SLOT_BONUS
        elif patreon_status == "Yellow Tier":
            marketlimitbonus = YELLOW_PATREON_SLOT_BONUS
        elif patreon_status == "Red Tier":
            marketlimitbonus = PATREON_SLOT_BONUS
        else:
            marketlimitbonus = 0
        markettext = f"{usedmarket}/{marketlimit}"
        if marketlimitbonus:
            markettext += f" (+ {marketlimitbonus}!)"
        embed.add_field(name="Market spaces", value=markettext, inline=True)
        if is_staff.lower() != "user":
            embed.set_footer(
                text=f"Holding: {hitem.capitalize().replace('-',' ')}",
                icon_url="https://cdn.discordapp.com/attachments/707730610650873916/773574461474996234/logo_mew.png",
            )
        else:
            embed.set_footer(text=f"Holding: {hitem.capitalize().replace('-',' ')}")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @discord.app_commands.describe(nickname="The Trainer Nickname to use.")
    async def trainernick(self, ctx, nickname: str):
        """Sets your trainer nickname."""
        val = nickname
        if any(word in val for word in ("@here", "@everyone", "http")):
            await ctx.send("Nope.")
            return
        if len(val) > 18:
            await ctx.send("Trainer nick too long!")
            return
        if re.fullmatch(r"^[ -~]*$", val) is None:
            await ctx.send("Unicode characters cannot be used in your trainer nick.")
            return
        if "|" in val:
            await ctx.send("`|` cannot be used in your trainer nick.")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            nick = await pconn.fetchval(
                "SELECT tnick FROM users WHERE u_id = $1", ctx.author.id
            )
            if nick is not None:
                await ctx.send("You have already set your trainer nick.")
                return
            user = await pconn.fetchval("SELECT u_id FROM users WHERE tnick = $1", val)
            if user is not None:
                await ctx.send("That nick is already taken. Try another one.")
                return
            await pconn.execute(
                "UPDATE users SET tnick = $1 WHERE u_id = $2", val, ctx.author.id
            )
        await ctx.send("Successfully Changed Trainer Nick")

    @commands.hybrid_command()
    @tradelock
    async def resetme(self, ctx):
        """Resets your account & all data - This Cannot be UNDONE!"""
        cooldown = (
            await ctx.bot.redis_manager.redis.execute(
                "HMGET", "resetcooldown", str(ctx.author.id)
            )
        )[0]

        if cooldown is None:
            cooldown = 0
        else:
            cooldown = float(cooldown.decode("utf-8"))

        if cooldown > time.time():
            reset_in = cooldown - time.time()
            cooldown = f"{round(reset_in)}s"
            await ctx.send(f"Command on cooldown for {cooldown}")
            return
        await ctx.bot.redis_manager.redis.execute(
            "HMSET", "resetcooldown", str(ctx.author.id), str(time.time() + 60 * 60 * 3)
        )

        prompts = [
            "Are you sure you want to reset your account? This cannot be undone.",
            (
                "Are you **absolutely certain**? This will reset **all of your pokemon**, "
                "**all of your credits and redeems**, and anything else you have done on the bot and "
                "**cannot be undone**.\nOnly click `Confirm` if you are **certain** you want this."
            ),
        ]
        for prompt in prompts:
            if not await ConfirmView(ctx, prompt).wait():
                await ctx.send("Canceling reset.")
                return
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "DELETE FROM redeemstore WHERE u_id = $1", ctx.author.id
            )
            await pconn.execute("DELETE FROM cheststore WHERE u_id = $1", ctx.author.id)
            await pconn.execute("DELETE FROM users WHERE u_id = $1", ctx.author.id)
        await ctx.send(
            "Your account has been reset. Start the bot again with `/start`."
        )
        await ctx.bot.get_partial_messageable(999442907465523220).send(ctx.author.id)

    @commands.hybrid_command()
    async def invite(self, ctx):
        embed = Embed(
            title="Invite Me", description="The invite link for MewBot", color=0xFFB6C1
        )

        # invite l
        embed.add_field(
            name="Invite",
            value="[Invite MewBot](https://discordapp.com/api/oauth2/authorize?client_id=519850436899897346&response_type=code&redirect_uri=https://discord.gg/mewbot&permissions=387136&scope=bot+applications.commands)",
        )
        embed.add_field(
            name="Official Server",
            value="[Join the Official Server](https://discord.gg/mewbot)",
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def region(
        self, ctx, reg: Literal["original", "alola", "galar", "hisui", "paldea"]
    ):
        """Change your region to allow your Pokémon evolve into regional forms."""
        if reg not in ("original", "alola", "galar", "hisui"):
            if reg == "paldea":
                await ctx.send("Coming... Join the Official Server for more info!")
                return
            await ctx.send(
                "That isn't a valid region! Select one of `original`, `alola`, `galar`, `hisui`, `paldea`."
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET region = $1 WHERE u_id = $2", reg, ctx.author.id
            )
        await ctx.send(f"Your region has been set to **{reg.title()}**.")

    #@commands.hybrid_command()
    @discord.app_commands.describe(user="A User to view their balance details.")
    async def bal(self, ctx, user: discord.User = None):
        """Shows your Balance & Lists credits, redeems, EV points, upvote points, and selected fishing rod."""
        if user is None:
            user = ctx.author
        async with ctx.bot.db[0].acquire() as tconn:
            details = await tconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", user.id
            )
            if details is None:
                await ctx.send(f"{user.name} has not started!")
                return
            if (
                not details["visible"]
                and user.id != ctx.author.id
                and ctx.author.id != ctx.bot.owner_id
            ):
                await ctx.send(
                    f"You are not permitted to see the Trainer card of {user.name}"
                )
                return
            if details["last_vote"] < time.time() - (36 * 60 * 60):
                vote_streak = 0
            else:
                vote_streak = details["vote_streak"]
            pokes = details["pokes"]
            visible = details["visible"]
            u_id = details["u_id"]
            redeems = details["redeems"]
            tnick = details["tnick"]
            uppoints = details["upvotepoints"]
            mewcoins = details["mewcoins"]
            evpoints = details["evpoints"]
            count = len(pokes)
            is_staff = details["staff"]
            region = details["region"]
            staffrank = await tconn.fetchval(
                "SELECT staff FROM users WHERE u_id = $1", user.id
            )
            hitem = details["held_item"]
            desc = f"{tnick if tnick is not None else user.name}'s\n__**Balances**__"
            desc += f"\n<:mewcoin:1010959258638094386>**Credits**: `{mewcoins:,}`"
            desc += f"\n<:redeem:1037942226132668417>**Redeems**: `{redeems:,}`"
            desc += f"\n<:evs:1029331432792915988>**EV Points**: `{evpoints:,}`"
            desc += f"\n<:upvote:1037942314691199089>**Upvote Points**: `{uppoints}`"
            desc += (
                f"\n<:upvotestreak:1037942367929503766>**Vote Streak**: `{vote_streak}`"
            )
            desc += f"\n**Holding**: `{hitem.capitalize().replace('-',' ')}`"
            desc += f"\n**Region**: `{region.capitalize()}`"
            embed = Embed(color=0xFFB6C1, description=desc)
            if is_staff.lower() != "user":
                embed.set_author(
                    name=f"Official Staff Member",
                    icon_url="https://cdn.discordapp.com/attachments/707730610650873916/843250286998192128/moshed-05-15-17-30-34.gif",
                )
                embed.add_field(
                    name="Bot Staff Rank",
                    value=f"{staffrank}",
                )
            else:
                embed.set_author(name=f"Trainer Information")
            view = discord.ui.View(timeout=60)

            async def check(interaction):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message(
                        content="You are not allowed to interact with this button.",
                        ephemeral=True,
                    )
                    return False
                return True

            view.interaction_check = check
            chest = discord.ui.Button(
                style=discord.ButtonStyle.gray, label="View chests"
            )

            async def chestcallback(interaction):
                await self.balance_chests(ctx, user)

            chest.callback = chestcallback
            view.add_item(chest)
            misc = discord.ui.Button(style=discord.ButtonStyle.gray, label="View misc")

            async def misccallback(interaction):
                await self.balance_misc(ctx, user)

            misc.callback = misccallback
            view.add_item(misc)
            await ctx.send(embed=embed, view=view)

    async def balance_chests(self, ctx, user: discord.User = None):
        """Lists the current chests you have to open."""
        if user is None:
            user = ctx.author
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", user.id
            )
            if details is None:
                await ctx.send(f"{user.name} has not started!")
                return
            if (
                not details["visible"]
                and user.id != ctx.author.id
                and ctx.author.id != ctx.bot.owner_id
            ):
                await ctx.send(
                    f"You are not permitted to see how many chests {user.name} has"
                )
                return
            inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", user.id
            )
            info = await pconn.fetchrow(
                "SELECT rare, mythic, legend FROM cheststore WHERE u_id = $1",
                ctx.author.id,
            )

        # running chest totals
        common = inv.get("common chest", 0)
        rare = inv.get("rare chest", 0)
        mythic = inv.get("mythic chest", 0)
        legend = inv.get("legend chest", 0)
        exalted = inv.get("exalted chest", 0)
        hitem = details["held_item"]
        tnick = details["tnick"]

        embed = Embed(
            title=f"{tnick if tnick is not None else user.name}'s Chests",
            color=0xFFB6C1,
        )
        embed.add_field(
            name="Common",
            value=f"<:cchest1:1010888643369500742><:cchest2:1010888709031350333>\n<:cchest2:1010888756540215297><:cchest4:1010888875536822353> {common}",
            inline=True,
        )
        embed.add_field(
            name="Rare",
            value=f"<:rchest1:1010889168802562078><:rchest2:1010889239988277269>\n<:rchest3:1010889292672942101><:rchest4:1010889342639677560> {rare}",
            inline=True,
        )
        embed.add_field(
            name="Mythic",
            value=f"<:mchest1:1010889412558717039><:mchest2:1010889464119300096>\n<:mchest3:1010889506838302821><:mchest4:1010889554418487347> {mythic}",
            inline=True,
        )
        embed.add_field(
            name="Legend",
            value=f"<:lchest1:1010889611318411385><:lchest2:1010889654800756797>\n<:lchest4:1010889740138061925><:lchest3:1010889697687511080> {legend}",
            inline=True,
        )

        #This is for the purchased chest
        #This table is only made when players buy a chest
        #So new players won't have it causing command to fail
        if info is not None:
            rare_count = info.get("rare",0)
            mythic_count = info.get("mythic",0)
            legend_count = info.get("legend", 0)
            embed.add_field(name="Exalted", value=f"Count: {exalted}", inline=True)
            embed.add_field(
                name="Purchased Chests",
                value=f"Rare: {rare_count}/5\nMythic: {mythic_count}/5\nLegend: {legend_count}/5",
                inline=True,
            )
        await ctx.send(embed=embed)

    async def balance_misc(self, ctx, user: discord.User = None):
        """
        Lists other miscellaneous data.

        Includes held item, pokemon owned, market slots, egg slots,
        bicycle, honey, gleam gems, IV mult, nature capsules,
        shiny multi, battle multi, and breeding multi.
        """
        if user is None:
            user = ctx.author
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", user.id
            )
            if details is None:
                await ctx.send(f"{user.name} has not started!")
                return
            if (
                not details["visible"]
                and user.id != ctx.author.id
                and ctx.author.id != ctx.bot.owner_id
            ):
                await ctx.send(
                    f"You are not permitted to see how many chests {user.name} has"
                )
                return
            pokes = details["pokes"]
            daycared = await pconn.fetchval(
                "SELECT count(*) FROM pokes WHERE id = ANY ($1) AND pokname = 'Egg'",
                pokes,
            )
            usedmarket = await pconn.fetchval(
                "SELECT count(id) FROM market WHERE owner = $1 AND buyer IS NULL",
                user.id,
            )
        bike = details["bike"]
        visible = details["visible"]
        u_id = details["u_id"]
        tnick = details["tnick"]
        dlimit = details["daycarelimit"]
        hitem = details["held_item"]
        marketlimit = details["marketlimit"]
        dets = details["inventory"]
        count = len(pokes)
        is_staff = details["staff"]
        hunt = details["hunt"]
        huntprogress = details["chain"]
        essence = details["essence"]
        patreon_status = await ctx.bot.patreon_tier(user.id)
        if patreon_status in ("Crystal Tier", "Sapphire Tier"):
            marketlimitbonus = CRYSTAL_PATREON_SLOT_BONUS
        elif patreon_status == "Silver Tier":
            marketlimitbonus = SILVER_PATREON_SLOT_BONUS
        elif patreon_status == "Yellow Tier":
            marketlimitbonus = YELLOW_PATREON_SLOT_BONUS
        elif patreon_status == "Red Tier":
            marketlimitbonus = PATREON_SLOT_BONUS
        else:
            marketlimitbonus = 0
        markettext = f"{usedmarket}/{marketlimit}"
        if marketlimitbonus:
            markettext += f" (+ {marketlimitbonus}!)"
        desc = f"**Held Item**: `{hitem}`"
        desc += f"\n**Pokemon Owned**: `{count:,}`"
        desc += f"\n**Market Slots**: `{markettext}`"
        desc += f"\n**Daycare Slots**: `{daycared}/{dlimit}`"
        desc += f"| **Terastal Essence**: `{essence['x']},{essence['y']}/125`"
        if hunt:
            desc += f"\n**Shadow Hunt**: {hunt} ({huntprogress}x)"
        else:
            desc += f"\n**Shadow Hunt**: Select with `/hunt`!"
        desc += f"\n**Bicycle**: {bike}"
        desc += "\n**General Inventory**\n"
        dets = ujson.loads(dets)
        dets.pop("coin-case", None) if "coin-case" in dets else None
        for item in dets:
            if item in ("common chest", "rare chest", "mythic chest", "legend chest"):
                continue
            if "breeding" in item:
                desc += f"{item.replace('-', ' ').capitalize()} `{dets[item]}` `({calculate_breeding_multiplier(dets[item])})`\n"
            elif "iv" in item:
                desc += f"{item.replace('-', ' ').capitalize()} `{dets[item]}` `({calculate_iv_multiplier(dets[item])})`\n"
            else:
                desc += f"{item.replace('-', ' ').capitalize()} `{dets[item]}`x\n"
        embed = Embed(color=0xFFB6C1, description=desc)
        if is_staff.lower() != "user":
            embed.set_author(
                name=f"{tnick if tnick is not None else user.name}'s Miscellaneous Balances",
                icon_url="https://cdn.discordapp.com/attachments/707730610650873916/773574461474996234/logo_mew.png",
            )
        else:
            embed.set_author(
                name=f"{tnick if tnick is not None else user.name}'s Miscellaneous Balances"
            )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Extras(bot))
