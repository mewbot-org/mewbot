import discord
import asyncpg
import textwrap
import asyncio
import random

from discord.ext import commands

from mewcogs.pokemon_list import *
from mewcogs.json_files import *
from mewutils.misc import *


class Orders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def order_ivs(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2", "iv", ctx.author.id
            )
        await ctx.send("Your Pokemon will now be ordered by their IVs!")

    @commands.hybrid_command()
    async def order_default(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2", "kek", ctx.author.id
            )
        await ctx.send("Your Pokemon orders have been reset!")

    @commands.hybrid_command()
    async def order_evs(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2", "ev", ctx.author.id
            )
        await ctx.send("Your Pokemon will now be ordered by their EVs!")

    @commands.hybrid_command()
    async def order_name(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2",
                "name",
                ctx.author.id,
            )
        await ctx.send("Your Pokemon will now be ordered by their Names!")

    @commands.hybrid_command()
    async def order_level(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2",
                "level",
                ctx.author.id,
            )
        await ctx.send("Your Pokemon will now be ordered by their Level!")


async def setup(bot):
    await bot.add_cog(Orders(bot))
