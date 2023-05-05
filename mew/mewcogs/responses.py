import discord
import asyncio
from discord.ext import commands
from mewcogs.pokemon_list import _


class Responses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if (
            member.guild.id == self.bot.official_server
            and self.bot.user.id == 519850436899897346
        ):
            e = discord.Embed(title="Welcome to the Mewbot's Official Server!")
            # e.description = "If you are a New Player or you just want to learn the basics of Mewbot, check out the tutorials category!\nStart here! <#572657758487314433>"
            e.description = "Thanks for joining! As customary please read the <#573514674625052703>\nCheck out <#519468626290540554> for some recent events, status updates, and various other topics.\nWe also have a <#572657758487314433> we suggest everyone checks out before asking questions in <#529322785080737792>\nThank you again for joining and hope you enjoy your time here!!"
            await member.send(embed=e)


async def setup(bot):
    await bot.add_cog(Responses(bot))
