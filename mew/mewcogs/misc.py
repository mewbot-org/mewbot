import discord
from discord.ext import commands

from mewcogs.pokemon_list import *
from mewcogs.json_files import *
from pokemon_utils.utils import evolve
import random
import urllib
import asyncio
import concurrent
import time
import traceback
from collections import defaultdict

GUILD_DEFAULT = {
    "prefix": ";",
    "disabled_channels": [],
    "redirects": [],
    "disabled_spawn_channels": [],
    "pin_spawns": False,
    "delete_spawns": False,
    "small_images": False,
    "silence_levels": False,
}

POKEMON_WITH_EGG_ABILITIES = {
    "Rapidash",
    "Talonflame",
    "Slugma",
    "Carkol",
    "Larvesta",
    "Coalossal",
    "Fletchinder",
    "Centiskorch",
    "Coalossal-Gmax",
    "Magmar",
    "Litwick",
    "Moltres",
    "Centiskorch-Gmax",
    "Magmortar",
    "Rolycoly",
    "Camerupt",
    "Ponyta",
    "Volcarona",
    "Lampent",
    "Sizzlipede",
    "Magcargo",
    "Chandelure",
    "Heatran",
    "Magby",
}


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # This might be better in Redis, but eh if someone wants to get .01% better rates by spam switching channels, let them
        self.user_cache = defaultdict(int)

    @commands.hybrid_command()
    async def slashinvite(self, ctx):
        """Command to allow users to reinvite the bot w/ slash command perms."""
        await ctx.send(
            "If you cannot see slash commands, kick me and reinvite me with the following invite link:\n"
            "<https://discordapp.com/api/oauth2/authorize?client_id=519850436899897346&permissions=387136&scope=bot+applications.commands>"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if not message.guild or not message.guild.me:
            return
        if message.author.bot:
            return
        if self.bot.botbanned(message.author.id):
            return
        if message.guild.id in (264445053596991498, 446425626988249089):
            return
        if not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if not message.channel.permissions_for(message.guild.me).embed_links:
            return

        if message.channel.id == 519466243342991362:
            #
            user = await self.bot.mongo_find(
                "users",
                {"user": message.author.id},
                default={"user": message.author.id, "progress": {}},
            )
            progress = user["progress"]
            progress["chat-general"] = progress.get("chat-general", 0) + 1
            await self.bot.mongo_update(
                "users", {"user": message.author.id}, {"progress": progress}
            )
            #
        if time.time() < self.user_cache[message.author.id]:
            return
        self.user_cache[message.author.id] = time.time() + 5
        async with self.bot.db[0].acquire() as pconn:
            try:
                if (
                    await pconn.fetchval(
                        "SELECT true FROM users WHERE u_id = $1", message.author.id
                    )
                    is None
                ):
                    return
                (
                    hatched_party_pokemon,
                    hatched_pokemon,
                    level_pokemon,
                ) = await pconn.fetchrow(
                    "SELECT party_counter($1), selected_counter($1), level_pokemon($1)",
                    message.author.id,
                )

                """ Check For Magma Armor, Flame body bleh"""
                party_pokemon = await pconn.fetch(
                    "SELECT pokname FROM pokes WHERE id IN (SELECT unnest(party) FROM users u WHERE u.u_id = $1)",
                    message.author.id,
                )
                exists = not POKEMON_WITH_EGG_ABILITIES.isdisjoint(
                    set([record["pokname"] for record in party_pokemon])
                )
                if exists and random.random() < 0.25:  # 25% Chance.
                    if message.author.id == 455277032625012737:
                        await message.channel.send("Hit the spot.")
                    (
                        hatched_party_pokemon,
                        hatched_pokemon,
                        level_pokemon,
                    ) = await pconn.fetchrow(
                        "SELECT party_counter($1), selected_counter($1), level_pokemon($1)",
                        message.author.id,
                    )
                """ TADA """
            except Exception:
                return
            response = ""
            if hatched_party_pokemon:
                for egg_name in hatched_party_pokemon:
                    #
                    user = await self.bot.mongo_find(
                        "users",
                        {"user": message.author.id},
                        default={"user": message.author.id, "progress": {}},
                    )
                    progress = user["progress"]
                    progress["hatch"] = progress.get("hatch", 0) + 1
                    await self.bot.mongo_update(
                        "users", {"user": message.author.id}, {"progress": progress}
                    )
                    #
                    response += f"Congratulations!\nYour {egg_name} Egg has hatched!\n"
                    chest_chance = not random.randint(0, 200)
                    if chest_chance:
                        await self.bot.commondb.add_bag_item(
                            message.author.id, "common_chest", 1, True
                        )
                        response += "It was holding a common chest!\n"
            if hatched_pokemon:
                #
                user = await self.bot.mongo_find(
                    "users",
                    {"user": message.author.id},
                    default={"user": message.author.id, "progress": {}},
                )
                progress = user["progress"]
                progress["hatch"] = progress.get("hatch", 0) + 1
                await self.bot.mongo_update(
                    "users", {"user": message.author.id}, {"progress": progress}
                )
                #
                response += (
                    f"Congratulations!\nYour {hatched_pokemon} Egg has hatched!\n"
                )
                chest_chance = not random.randint(0, 200)
                if chest_chance:
                    await self.bot.commondb.add_bag_item(
                        message.author.id, "common_chest", 1, True
                    )
                    response += "It was holding a common chest!\n"
            if level_pokemon:
                pokemon_details = await pconn.fetchrow(
                    "SELECT users.silenced, pokes.* FROM users INNER JOIN pokes on pokes.id = (SELECT selected FROM users WHERE u_id = $1) AND users.u_id = $1",
                    message.author.id,
                )
                silenced = pokemon_details.get("silenced")
                guild_details = await self.bot.db[1].guilds.find_one(
                    {"id": message.guild.id}
                )
                if guild_details:
                    silenced = silenced or guild_details["silence_levels"]
                if not silenced:
                    response += f"{message.author.mention} Your {level_pokemon} has leveled up!\n"
                try:

                    class FakeContext:
                        def __init__(self, bot, message):
                            self.message = message
                            self.guild = message.guild
                            self.channel = message.channel
                            self.author = message.author
                            self.bot = bot
                            self.command = None

                        async def send(self, *args, **kwargs):
                            return await self.channel.send(*args, **kwargs)

                    await evolve(
                        FakeContext(
                            self.bot, message
                        ),  # Don't ask to evolve in this case
                        self.bot,
                        pokemon_details,
                        message.author,
                        channel=message.channel,
                    )
                except Exception as e:
                    self.bot.logger.exception("Error in evolve", exc_info=e)
            if response:
                try:
                    await message.channel.send(
                        embed=discord.Embed(description=response, color=0xFF49E6)
                    )
                except discord.HTTPException:
                    pass
                return

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if self.bot.user.id == 519850436899897346:
            guild_data = GUILD_DEFAULT.copy()
            guild_data["id"] = guild.id
            await self.bot.db[1].guilds.insert_one(guild_data)
            owner = await self.bot.fetch_user(guild.owner_id)
            guild_name = guild.name
            owner_id = owner.id
            owner_name = owner.name
            member_count = "??"
            e = discord.Embed(
                title="Thank you for adding me to your server!!", color=0xEDD5ED
            )
            e.add_field(
                name="Tutorial",
                value="Get a tutorial of how to use Mewbot by using `/tutorial`.",
            )
            e.add_field(
                name="Manage Spawns",
                value="Manage spawns in your server by using `/spawns disable` to disable spawns in a channel, or `/spawns redirect` to redirect spawns to a specific channel.",
            )
            e.add_field(
                name="Help",
                value="If you need any more help, join the official server with the link in `/invite` and ask for help in #questions!",
            )
            try:
                await owner.send(embed=(e))
            except Exception:
                pass
            await self.bot.get_partial_messageable(1110257863059849256).send(
                f"__**Server Join**__\N{SMALL BLUE DIAMOND}- {owner_name} - ``{owner_id}`` added Mewbot to\n{guild_name} - `{guild.id}`\n"
            )
            # await self.bot.log(
            #     929516766965694545,
            #     f"**New Join:**\n**Server Name** = `{guild_name}`\n**Ownerid id** = `{owner_id}`\n**Owner name** = `{owner_name}`\n**Members** = `{member_count}`",
            # )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if self.bot.user.id == 519850436899897346:
            await self.bot.db[1].guilds.delete_one({"id": guild.id})
            owner = await self.bot.fetch_user(guild.owner_id)
            await self.bot.owner.send(
                f"""
                             {
                                 owner.mention
                             } kicked mewbot
                             """
            )

    @commands.hybrid_command()
    async def donate(self, ctx):
        "Support MewBot & get Credit and Redeem Rewards! (Also comes with perks in our Official Server)."
        # User "is unable to control himself", so is blocked from using the command
        if ctx.author.id == 499740738138013696:
            await ctx.send(
                "Sorry, you are not currently able to use this command. Contact Dylee if you think this block should be removed."
            )
            return
        name = ctx.author.name
        if " " in name:
            name = name.replace(" ", "")
        e = discord.Embed(title="Donate to the Bot Here!", color=0xFFB6C1)
        donation_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_donations&notify_url=https://api.mewbot.xyz/paypal&business=vintagedust@live.com&lc=US&item_name=MewBot-Donation-from-{ctx.author.id}&currency_code=USD&custom={ctx.author.id}"

        payload = {"user_name": ctx.author.name, "user_id": ctx.author.id}
        # donation_url = f"https://mewbot.xyz/donate?{urllib.parse.urlencode(payload)}"

        # e.add_field(name="READ THIS", value="We are currently experiencing problems with the automatic rewards from donations. Heres our temporary work-around.\n 1.Please use this [link](https://mewbot.wiki/en/Donations) to donate via paypal.\n2.Then DM Sky or join the [official server](https://discord.gg/mewbot) and ask in questions.\n3. Have a SS of donation ready.")
        e.add_field(name="Donation Link", value=f"[Donate Here!]({donation_url})\n")
        e.add_field(
            name="Patreon",
            value=f"**[Become a Patreon and benefit from some awesome rewards.](https://www.patreon.com/mewbotxyz?fan_landing=true)**\n*Patreon is not the same as standard donations, and has totally unique benefits and rewards-see the link above for information on the tiers available.",
            inline=False,
        )
        e.set_footer(
            text="You will receive 1 Redeem + 2,000 credits for every USD donated."
        )
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        self.bot.logger.error(
            "Error in event or general bot (found in on_error)", exc_info=True
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # await ctx.bot.cmds_file.write(f"Command used => {ctx.command} - User -> {ctx.author.name}({ctx.author.id})\n")
        # await ctx.bot.cmds_file.flush()
        ctx.bot.commands_used[ctx.command.name] = (
            ctx.bot.commands_used.get(ctx.command.name, 0) + 1
        )

        if ctx.command.cog_name == "MewBotAdmin":
            await ctx.bot.log(
                695322994725355621,
                f"{ctx.author.name} - {ctx.author.id} used {ctx.command.name} command\nArguments - {ctx.args}\n{ctx.kwargs}",
            )
        if ctx.command.cog_name == "Settings":
            await self.bot.load_guild_settings()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # TODO: This listener overrides the default command error handler.
        # While that is fine right now, since exceptions are re-raised (as an exception in this listener)
        # when they are unhandled, in the future error handling currently covered by this listener
        # should be a part of the code causing that error. Once that is done, this listener should probably
        # be removed or swapped to have better handling.
        ignored_errors = (
            commands.errors.CommandNotFound,
            commands.errors.MissingPermissions,
            concurrent.futures._base.TimeoutError,
            commands.CheckFailure,
            commands.DisabledCommand,
            commands.MaxConcurrencyReached,
        )
        if isinstance(error, ignored_errors):
            return
        if isinstance(error, discord.errors.Forbidden):
            try:
                await ctx.author.send(
                    f"I do not have Permissions to use in {ctx.channel}"
                )
            except discord.HTTPException:
                pass
            return
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = f"{error.retry_after:.2f}s"
            try:
                await ctx.channel.send(f"Command on cooldown for {cooldown}")
            except Exception:
                pass
            return
        help_errors = (
            commands.errors.MissingRequiredArgument,
            commands.errors.BadArgument,
        )
        if isinstance(error, help_errors):
            command = ctx.command
            try:
                await ctx.send(
                    f"That command doesn't look quite right...\n"
                    f"Syntax: `{ctx.prefix}{command.qualified_name} {command.signature}`\n\n"
                    f"For more help, see `{ctx.prefix}help {command.cog_name}`"
                )
            except:
                pass
            return
        if isinstance(error, commands.errors.CommandInvokeError):
            # This should get the actual error behind the CommandInvokeError
            error = error.__cause__ if error.__cause__ else error
            if "TimeoutError" in str(error) or "Forbidden" in str(error):
                return
            if ctx.command.cog_name in ("battle", "duel"):
                try:
                    await ctx.send(
                        "Please make sure you have selected a Pokemon, no eggs are in your party, your party is full, and the same for your opponent"
                    )
                except:
                    pass
                return
            ctx.bot.traceback = (
                f"Exception in command '{ctx.command.qualified_name}'\n"
                + "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
            )
        # Since this overrides the default command listener, this raise sends this error to the
        # listener error handler as an exception in the "on_command_error" listener so it can be
        # printed to console.
        ctx.bot.logger.exception(type(error).__name__, exc_info=error)


async def setup(bot):
    await bot.add_cog(Misc(bot))
