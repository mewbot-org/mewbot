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

    @commands.hybrid_group()
    async def order(self, ctx):
        ...

    @order.command()
    async def ivs(self, ctx):
        """Order your Pokemon according to their IVs"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2", "iv", ctx.author.id
            )
        await ctx.send("Your Pokemon will now be ordered by their IVs!")

    @order.command()
    async def default(self, ctx):
        """Remove ordering"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2", "kek", ctx.author.id
            )
        await ctx.send("Your Pokemon orders have been reset!")

    @order.command()
    async def evs(self, ctx):
        """Order your Pokemon according to their EVs"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2", "ev", ctx.author.id
            )
        await ctx.send("Your Pokemon will now be ordered by their EVs!")

    @order.command()
    async def name(self, ctx):
        """Order your Pokemon according to their names alphabetically."""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2",
                "name",
                ctx.author.id,
            )
        await ctx.send("Your Pokemon will now be ordered by their Names!")

    @order.command()
    async def level(self, ctx):
        """Order your Pokemon according to their levels"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET user_order = $1 WHERE u_id = $2",
                "level",
                ctx.author.id,
            )
        await ctx.send("Your Pokemon will now be ordered by their Level!")


async def setup(bot):
    await bot.add_cog(Orders(bot))
