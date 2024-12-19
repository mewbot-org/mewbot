from discord.ext import commands


class Auctions(commands.Cog): ...


async def setup(bot):
    await bot.add_cog(Auctions(bot))
