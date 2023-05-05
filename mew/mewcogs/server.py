import discord
from discord.ext import commands

from mewcogs.json_files import *
from mewutils.misc import pagify, MenuView


def default_factory():
    return {
        "prefix": ";",
        "disabled_channels": [],
        "redirects": [],
        "disabled_spawn_channels": [],
        "pin_spawns": False,
        "delete_spawns": False,
        "small_images": False,
        "silence_levels": False,
    }


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_current(self, ctx):
        current_setting = await ctx.bot.mongo_find("guilds", {"id": ctx.guild.id})
        if not current_setting:
            current_setting = default_factory()
            current_setting["id"] = ctx.guild.id
            await ctx.bot.mongo_update("guilds", {"id": ctx.guild.id}, current_setting)
        return current_setting

    @commands.hybrid_group()
    async def spawns(self, ctx):
        """
        Spawns base command.
        """
        pass

    # @spawns.group()
    # async def mention(self, ctx):
    #     ...

    @spawns.command(name="mention")
    async def spawns_mention_spawn(self, ctx):
        """Toggles mention spawns setting - (catch pokemon via mentions | @mewbot <pokemon_name>)"""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"mention_spawns": not current_setting.get("mention_spawns", False)},
        )

        current_setting["mention_spawns"] = not current_setting.get(
            "mention_spawns", False
        )

        if current_setting.get("mention_spawns", False):
            await ctx.send("Mention spawns are now enabled.")
        else:
            await ctx.send("Mention spawns are now disabled.")

    @spawns.group()
    async def auto(self, ctx):
        ...

    @auto.command(name="delete")
    async def auto_delete(self, ctx):
        """
        Deletes the spawn image when you catch a Pokemon.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"delete_spawns": not current_setting["delete_spawns"]},
        )
        await ctx.send(
            f"Spawns will {'be deleted' if not current_setting['delete_spawns'] else 'not be deleted'} in all channels"
        )

    @auto.command(name="pin")
    async def auto_pin(self, ctx):
        """
        Automatically pins rare spawns.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"pin_spawns": not current_setting["pin_spawns"]},
        )
        await ctx.send(
            f"Rare Spawns will {'be pinned' if not current_setting['pin_spawns'] else 'not be pinned'} in all channels"
        )

    @spawns.group()
    async def redirect(self, ctx):
        ...

    @redirect.command(name="add")
    @discord.app_commands.describe(
        channel="The channel to add to the spawns redirect list."
    )
    async def redirect_add(self, ctx, channel: discord.TextChannel = None):
        """Adds a channel for spawns to redirect to."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        if not channel:
            channel = ctx.channel
        current_setting = await self.get_current(ctx)
        channels = set(current_setting["redirects"])
        channels.add(channel.id)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"redirects": list(channels)},
        )
        await ctx.send(f"Successfully added {channel} to the spawn redirects list.")

    @redirect.command(name="remove")
    @discord.app_commands.describe(
        channel="The channel to remove from the spawns redirect list."
    )
    async def redirect_remove(self, ctx, channel: discord.TextChannel = None):
        """Removes a channel for spawns to redirect to."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        if not channel:
            channel = ctx.channel
        current_setting = await self.get_current(ctx)
        channels = set(current_setting["redirects"])
        if channel.id not in channels:
            await ctx.send(
                "That channel is not in the redirect list! Use `/redirect clear` to clear all redirects."
            )
            return
        channels.remove(channel.id)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"redirects": list(channels)},
        )
        await ctx.send(f"Successfully removed {channel} from the spawn redirects list.")

    @redirect.command(name="clear")
    async def redirect_clear(self, ctx):
        """Resets the spawns redirect list."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        await ctx.bot.mongo_update("guilds", {"id": ctx.guild.id}, {"redirects": []})
        await ctx.send("All spawn redirects were removed.")

    @commands.hybrid_group(name="commands")
    async def _commands(self, ctx):
        """
        Commands base command
        """
        ...

    @_commands.command()
    async def disable(self, ctx, channel: discord.TextChannel = None):
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        if not channel:
            channel = ctx.channel
        current_setting = await self.get_current(ctx)
        disabled = set(current_setting["disabled_channels"])
        if channel.id in disabled:
            await ctx.send(f"Commands are already disabled in {channel}.")
            return
        disabled.add(channel.id)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"disabled_channels": list(disabled)},
        )
        await ctx.send(f"Successfully disabled commands in {channel}.")
        await ctx.bot.load_bans()

    @_commands.command()
    async def enable(self, ctx, channel: discord.TextChannel = None):
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        if not channel:
            channel = ctx.channel
        current_setting = await self.get_current(ctx)
        if channel.id not in current_setting["disabled_channels"]:
            await ctx.send(f"{channel} is already enabled.")
            return
        disabled = set(current_setting["disabled_channels"])
        disabled.remove(channel.id)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"disabled_channels": list(disabled)},
        )
        await ctx.send(f"Successfully enabled commands in {channel}.")
        await ctx.bot.load_bans()

    @spawns.command(name="disable")
    @discord.app_commands.describe(channel="The channel to disable spawns in.")
    async def spawns_disable(self, ctx, channel: discord.TextChannel = None):
        """Disables spawns in a channel."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        if not channel:
            channel = ctx.channel
        current_setting = await self.get_current(ctx)
        disabled = set(current_setting["disabled_spawn_channels"])
        if channel.id in disabled:
            await ctx.send(f"Spawns are already disabled in {channel}.")
            return
        disabled.add(channel.id)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"disabled_spawn_channels": list(disabled)},
        )
        await ctx.bot.load_bans()
        await ctx.send(f"Successfully disabled spawns in {channel}.")

    @spawns.command(name="enable")
    @discord.app_commands.describe(channel="The channel to enable spawns in.")
    async def spawns_enable(self, ctx, channel: discord.TextChannel = None):
        """Enables spawns in a channel."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        if not channel:
            channel = ctx.channel
        current_setting = await self.get_current(ctx)
        if channel.id not in current_setting["disabled_spawn_channels"]:
            await ctx.send(f"Spawns are already enabled in {channel}.")
            return
        disabled = set(current_setting["disabled_spawn_channels"])
        disabled.remove(channel.id)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"disabled_spawn_channels": list(disabled)},
        )
        await ctx.bot.load_bans()
        await ctx.send(f"Successfully enabled spawns in {channel}.")

    @spawns.command(name="small")
    async def spawns_small(self, ctx):
        """Toggle smaller spawn embeds in this guild."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"small_images": not current_setting["small_images"]},
        )
        await ctx.send(
            f"Spawn messages will now be {'small' if not current_setting['small_images'] else 'normal sized'} in this server."
        )

    @spawns.command(name="check")
    async def spawns_check(self, ctx):
        """Check spawn status for channels in this guild."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        disabled_channels = current_setting["disabled_spawn_channels"]
        redirect_channels = current_setting["redirects"]
        any_redirects = bool(redirect_channels)
        msg = ""
        for channel in ctx.guild.text_channels:
            name = channel.name
            if len(name) > 22:
                name = name[:19] + "..."
            name = name.ljust(22)
            perms = channel.permissions_for(ctx.guild.me)
            read = perms.read_messages
            send = perms.send_messages
            embeds = perms.embed_links
            enabled = channel.id not in disabled_channels
            redirect = channel.id in redirect_channels
            if not (read and send and embeds and enabled):
                spawns = "\N{CROSS MARK}"
            elif any_redirects and not redirect:
                spawns = "\N{RIGHTWARDS ARROW WITH HOOK}\N{VARIATION SELECTOR-16}"
            else:
                spawns = "\N{WHITE HEAVY CHECK MARK}"
            read = "\N{WHITE HEAVY CHECK MARK}" if read else "\N{CROSS MARK}"
            send = "\N{WHITE HEAVY CHECK MARK}" if send else "\N{CROSS MARK}"
            embeds = "\N{WHITE HEAVY CHECK MARK}" if embeds else "\N{CROSS MARK}"
            enabled = "\N{WHITE HEAVY CHECK MARK}" if enabled else "\N{CROSS MARK}"
            msg += f"{name}|  {spawns}  ||  {read}   |  {send} |  {embeds}   |  {enabled}\n"
        embed = discord.Embed(
            title="Spawn Checker", colour=random.choice(ctx.bot.colors)
        )
        pages = pagify(msg, per_page=25, base_embed=embed)
        for page in pages:
            page.description = f"```\nName                  | Spawn || Read  | Send | Embed |Enable\n{page.description}```"
        await MenuView(ctx, pages).start()

    @commands.hybrid_group()
    async def silence(self, ctx):
        ...

    @silence.command()
    async def user(self, ctx):
        """Silence Level up messages for yourself."""
        async with ctx.bot.db[0].acquire() as pconn:
            state = await pconn.fetchval(
                "UPDATE users SET silenced = NOT silenced WHERE u_id = $1 RETURNING silenced",
                ctx.author.id,
            )
        state = "off" if state else "on"
        await ctx.send(
            f"Successfully toggled {state} level up messages for your Pokémon!"
        )

    @silence.command()
    async def server(self, ctx):
        """Toggle level up messages in this server."""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send(
                "You are not allowed to manage this setting. You need to have `manage_messages` permission to do so."
            )
            return
        current_setting = await self.get_current(ctx)
        state = not current_setting["silence_levels"]
        await ctx.bot.mongo_update(
            "guilds",
            {"id": ctx.guild.id},
            {"silence_levels": state},
        )
        state = "off" if state else "on"
        await ctx.send(
            f"Successfully toggled {state} level up messages in this server!"
        )


async def setup(bot):
    await bot.add_cog(Settings(bot))
