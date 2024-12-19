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
        await self.msg.edit(
            content="You took too long to pick a nitro reward.", embed=None, view=None
        )
        await ctx.bot.redis_manager.redis.execute(
            "LREM", "nitrorace", "1", str(ctx.author.id)
        )

    @discord.ui.select(
        placeholder="Choose a reward for boosting!",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="1 - Legend chest - x5",
            ),
            discord.SelectOption(
                label="2 - Battle/shiny multi - x5\nBreed/IV multi - x3",
            ),
            discord.SelectOption(
                label="3 - Redeems - x10",
            ),
        ],
    )
    async def callback(self, interaction, select):
        ctx = self.ctx
        choice = int(self.children[0].values[0][0])
        await ctx.bot.db[1].boosters.update_one(
            {}, {"$push": {"boosters": ctx.author.id}}
        )
        async with interaction.client.db[0].acquire() as pconn:
            inventory = await pconn.fetchrow(
                "SELECT * FROM account_bound WHERE u_id = $1",
                ctx.author.id,
            )
            inventory = dict(inventory)
            if choice == 1:
                await interaction.client.commondb.add_bag_item(
                    ctx.author.id, "legend_chest", 5, True
                )
            elif choice == 2:
                battle_multi = min(50, inventory["battle_multiplier"] + 5)
                shiny_multi = min(50, inventory["shiny_multiplier"] + 5)
                iv_multi = min(50, inventory["iv_multiplier"] + 3) + 3
                breeding_multi = min(50, inventory["breeding_multiplier"] + 3)

                await pconn.execute(
                    "UPDATE account_bound SET battle_multiplier = $1, shiny_multiplier = $2, iv_multiplier = $3, breeding_multiplier = $4 WHERE u_id = $5",
                    battle_multi,
                    shiny_multi,
                    iv_multi,
                    breeding_multi,
                    ctx.author.id,
                )
            elif choice == 3:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + 10 WHERE u_id = $1",
                    ctx.author.id,
                )
        await self.msg.edit(
            embed=make_embed(
                title=f"You have received\n{CHOICES[choice-1]}\n**Can be claimed monthly!**"
            ),
            view=None,
        )
        await ctx.bot.redis_manager.redis.execute(
            "LREM", "nitrorace", "1", str(ctx.author.id)
        )
        self.stop()


class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_task = asyncio.create_task(self.initialize())

    async def initialize(self):
        await self.bot.redis_manager.redis.execute("LPUSH", "nitrorace", "123")

    @commands.hybrid_group()
    async def nitro(self, _): ...

    @nitro.command()
    async def claim(self, ctx):
        """Claim rewards for Boosting our Official Server!"""
        if ctx.guild != ctx.bot.official_server:
            await ctx.send(
                "You can only use this command in the Mewbot Official Server."
            )
            return
        if ctx.bot.booster_role not in ctx.author.roles:
            await ctx.send(
                "You can only use this command if you have nitro boosted this server."
            )
            return

        boosters = (await ctx.bot.db[1].boosters.find_one())["boosters"]

        in_process = [
            int(id_)
            for id_ in await self.bot.redis_manager.redis.execute(
                "LRANGE", "nitrorace", "0", "-1"
            )
            if id_.decode("utf-8").isdigit()
        ]

        if ctx.author.id in boosters:
            await ctx.send("You have already claimed Nitro Boost!")
            return

        if ctx.author.id in in_process:
            await ctx.send(
                "You are already in the process of claiming your Nitro Boost!"
            )
            return

        await self.bot.redis_manager.redis.execute(
            "LPUSH", "nitrorace", str(ctx.author.id)
        )

        async with ctx.bot.db[0].acquire() as pconn:
            u_id = await pconn.fetchval(
                "SELECT u_id FROM users WHERE u_id = $1", ctx.author.id
            )

        if u_id is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            await self.bot.redis_manager.redis.execute(
                "LREM", "nitrorace", "1", str(ctx.author.id)
            )
            return
        # Pick reward

        view = ChoicesView(ctx=ctx)
        msg = await ctx.send(
            embed=make_embed(title="Choose your desired Nitro Boost reward."), view=view
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
        await ctx.bot.db[1].boosters.update_one(
            {"key": "boosters"}, {"$set": {"boosters": []}}
        )
        await ctx.send("Reset Boosts for this month")


async def setup(bot):
    await bot.add_cog(Boost(bot))
