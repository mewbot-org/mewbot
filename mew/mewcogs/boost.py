import discord
from discord.ext import commands
from mewutils.checks import check_owner
from mewcogs.json_files import make_embed

import asyncio

CHOICES = (
    "Rare chest - x1",
    "Battle/shiny multi - x5\nBreed/IV multi - x3",
    "Credits - 150,000\nRedeems - x3",
)

class ChoicesView(discord.ui.View):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(timeout=60)
    
    def set_message(self, msg: discord.Message):
        self.msg = msg

    async def on_timeout(self):
        ctx = self.ctx
        await self.msg.edit(content="You took too long to pick a nitro reward.", embed=None, view=None)
        await ctx.bot.redis_manager.redis.execute(
            "LREM", "nitrorace", "1", str(ctx.author.id)
        )

    @discord.ui.select(
        placeholder = "Choose a reward for boosting!",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(
                label = "1 - Rare chest - x1",
            ),discord.SelectOption(
                label =  "2 - Battle/shiny multi - x5\nBreed/IV multi - x3",
            ),discord.SelectOption(
                label =  "3 - Credits - 150,000\nRedeems - x3",
            ),
        ]
    )

    async def callback(self, interaction, select):
        ctx = self.ctx
        choice = int(self.children[0].values[0][0])
        await ctx.bot.db[1].boosters.update_one({}, {"$push": {"boosters": ctx.author.id}})
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if choice == 1:
                inventory["rare chest"] = inventory.get("rare chest", 0) + 1
            elif choice == 2:
                inventory["battle-multiplier"] = min(50, inventory.get("battle-multiplier", 0) + 5)
                inventory["shiny-multiplier"] = min(50, inventory.get("shiny-multiplier", 0) + 5)
                inventory["iv-multiplier"] = min(50, inventory.get("iv-multiplier", 0) + 3)
                inventory["breeding-multiplier"] = min(50, inventory.get("breeding-multiplier", 0) + 3)
            elif choice == 3:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + 3, mewcoins = mewcoins + 150000 WHERE u_id = $1", ctx.author.id
                )
            await pconn.execute(
                "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                inventory,
                ctx.author.id,
            )
        await self.msg.edit(embed=make_embed(title=f"You have received\n{CHOICES[choice-1]}\n**Can be claimed monthly!**"), view=None)
        await ctx.bot.redis_manager.redis.execute("LREM", "nitrorace", "1", str(ctx.author.id))
        self.stop()

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_task = asyncio.create_task(self.initialize())

    async def initialize(self):
        await self.bot.redis_manager.redis.execute("LPUSH", "nitrorace", "123")

    @commands.hybrid_group()
    async def nitro(self, _):
        ...

    @nitro.command()
    async def claim(self, ctx):
        """Claim rewards for Boosting our Official Server!"""
        if ctx.guild.id != ctx.bot.official_server:
            await ctx.send("You can only use this command in the Mewbot Official Server.")
            return
        if ctx.bot.BOOSTER_ROLE not in [x.id for x in ctx.author.roles]:
            await ctx.send("You can only use this command if you have nitro boosted this server.")
            return

        boosters = (await ctx.bot.db[1].boosters.find_one())["boosters"]

        in_process = [
            int(id_)
            for id_ in await self.bot.redis_manager.redis.execute("LRANGE", "nitrorace", "0", "-1")
            if id_.decode("utf-8").isdigit()
        ]

        if ctx.author.id in boosters:
            await ctx.send("You have already claimed Nitro Boost!")
            return

        if ctx.author.id in in_process:
            await ctx.send("You are already in the process of claiming your Nitro Boost!")
            return

        await self.bot.redis_manager.redis.execute("LPUSH", "nitrorace", str(ctx.author.id))

        async with ctx.bot.db[0].acquire() as pconn:
            u_id = await pconn.fetchval("SELECT u_id FROM users WHERE u_id = $1", ctx.author.id)

        if u_id is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            await self.bot.redis_manager.redis.execute(
                "LREM", "nitrorace", "1", str(ctx.author.id)
            )
            return
        # Pick reward

        view = ChoicesView(ctx = ctx)
        msg = await ctx.send(
            embed = make_embed(title="Choose your desired Nitro Boost reward."), view=view
        )
        view.set_message(msg)

    @nitro.command()
    @check_owner()
    async def rmv(self, ctx, id: int):
        """Remove a Nitro Boost from the list"""
        # Dont touch this shit if you seeing this
        boosters_collection = ctx.bot.db[1].boosters
        boosters = (await boosters_collection.find_one())["boosters"]
        boosters.remove(id)
        await ctx.bot.db[1].boosters.update_one(
            {"key": "boosters"}, {"$set": {"boosters": boosters}}
        )
        await ctx.send(f"Reset boost for {id}")

    @nitro.command()
    @check_owner()
    async def reset(self, ctx):
        """Reset all Nitro Boosts"""
        boosters_collection = ctx.bot.db[1].boosters
        boosters = (await ctx.bot.db[1].boosters.find_one())["boosters"]
        await ctx.bot.db[1].boosters.update_one({"key": "boosters"}, {"$set": {"boosters": []}})
        await ctx.send("Reset Boosts for this month")


async def setup(bot):
    await bot.add_cog(Boost(bot))
