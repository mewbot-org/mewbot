from mewcogs.pokemon_list import *
from mewcogs.json_files import *
from discord.ext import commands
from pprint import pprint
from mewcogs.pokemon_list import _
import time

wait_cache = {}
immune_ids = (
    455277032625012737,  # dylee
    334155028170407949,
)


class Cooldown(commands.Cog):
    def get_command_cooldown(self, command):
        return 3
        commands_cooldown = {
            "duel": 15,
            "breed": 35,
        }
        return commands_cooldown.get(command, 3)

    async def bot_check(self, ctx):
        if ctx.author.id in immune_ids:
            return True

        if ctx.guild:
            if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
                return False
            if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
                await ctx.send(
                    "I require `embed_links` permission in order to function properly. Please give me that permission and try again."
                )
                return False
        if ctx.author.id in wait_cache and not ctx.command.parent:
            wait = wait_cache.get(ctx.author.id)
            if wait > time.time():
                secs = wait - time.time()
                cooldown = f"{round(secs)}s"
                try:
                    await ctx.channel.send(f"Command on cooldown for {cooldown}")
                except Exception:
                    pass
                return
            else:
                wait_cache[ctx.author.id] = time.time() + 3
                return True
        else:
            wait_cache[ctx.author.id] = time.time() + 3
            return True


async def setup(bot):
    await bot.add_cog(Cooldown())
