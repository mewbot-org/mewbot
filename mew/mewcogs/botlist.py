import discord
from discord.ext import tasks, commands
from mewutils.checks import check_admin
import aiohttp
import asyncio
import os
import logging
import ujson
from typing import Optional

botlist_tokens = {
    "fateslist.xyz": os.environ["FATESLIST"],
    "discordbotlist.com": os.environ["DBLPOST"],
    "bots.ondiscord.xyz": "", # TODO: Get tokens for both lists
    "top.gg": os.environ["TOPGG"]
}

class BotList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if self.bot.cluster["id"] != 1:
            self.enabled = False
        else:
            self.enabled = True
            self.botblock.start()
        self.botblock_url = "https://botblock.org/api/count"

    async def _guild_count(self) -> Optional[int]:
        """Handle clustering (this code was made by flame and was just made a function). If this returns None, ignore the whole guild count post"""
        launcher_res = await self.bot.handler("statuses", 1, scope="launcher")
        if not launcher_res:
            return None # Ignore this round
        processes = len(launcher_res[0])
        body = "return len(bot.guilds)"
        eval_res = await self.bot.handler(
            "_eval", processes, args={"body": body, "cluster_id": "-1"}, scope="bot", _timeout=5
        )
        if not eval_res:
            return None
        guild_count = 0
        for response in eval_res:
            if response["message"]:
                guild_count += int(response["message"])
        return guild_count

    async def _shard_count(self) -> Optional[int]:
        """Return shard count. In case clustering solution changes, you can just change this"""
        return self.bot.shard_count

    async def _botblock_poster(self):
        if self.bot.user.id != 519850436899897346:
            return False, "Not running on Mewbot"
        guild_count = await self._guild_count()
        if not guild_count:
            return False, "Failed to get guild count" # Wait
        
        shard_count = await self._shard_count()
        if not shard_count:
            return False, "Failed to get shard count" # Wait

        botblock_base_json = {"bot_id": str(self.bot.user.id), "server_count": guild_count, "shard_count": shard_count}
        botblock_json = {**botblock_base_json, **botlist_tokens} # Copy all botlist tokens to botblack base JSON
        self.bot.logger.debug(f"Posting botblock stats with JSON {botblock_base_json} and full JSON of {botblock_json}")

        async with aiohttp.ClientSession() as session:
            async with session.post(self.botblock_url, json = botblock_json) as res:
                response = await res.json()
                if res.status != 200:
                    msg = f"Got a non 200 status code trying to post to BotBlock.\n\nResponse: {response}\n\nStatus: {res.status}"
                    self.bot.logger.warn(msg)
                    return False, msg
                self.bot.logger.info("SUCCESS: Successfully posted to BotBlock. Should be propogating to all lists now")
                return True, response

    @tasks.loop(seconds = 60 * 45) 
    async def botblock(self):
        await self.bot.wait_until_clusters_ready()
        await self._botblock_poster() 

    @commands.hybrid_command()
    async def poststats(self, ctx):
        if ctx.author.id not in (
            790722073248661525, 
            473541068378341376, 
            455277032625012737, 
            563808552288780322,
        ):
            return

        await ctx.send("Going to post stats now!")  
        success, msg = await self._botblock_poster()
        if not success:
            return await ctx.send(f"**Error In Posting Stats To BotBlock**\n\n**Error: **{msg}")
        await ctx.send("**Successful Posts**")
        for botlist, data in msg["success"].items():
            await ctx.send(f"{botlist}: {data}")
        await ctx.send("**Failed Lists**")
        for botlist, data in msg["failure"].items():
            await ctx.send(f"{botlist}: {data}")


    def cog_unload(self):
        self.botblock.cancel()

async def setup(bot):
    await bot.add_cog(BotList(bot))
