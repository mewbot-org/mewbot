import discord
from discord.ext import commands

from mewcogs.json_files import *


class Missions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def missions(self, ctx):
        """
        Missions commands.
        """
        pass

    @missions.command(name="list")
    async def mission_list(self, ctx):
        """List all missions available to you"""
        raw = await ctx.bot.db[1].missions.find_one()
        if raw is None:
            await ctx.send(
                "Missions are resetting, please wait a few minutes and try again!"
            )
            return
        primary, secondary = raw["missions"]
        user = await ctx.bot.mongo_find(
            "users",
            {"user": ctx.author.id},
            default={"user": ctx.author.id, "progress": {}},
        )
        primary_text = ctx.bot.primaries.get(primary[0])[0]
        secondary_text = ctx.bot.secondaries.get(secondary[0])[0]
        progress = user["progress"]
        primary_completed = (
            "<a:cuscheck:534740177147396097>"
            if progress.get(primary[0], 0) >= primary[1]
            else "<a:cuscross:529192535642603530>"
        )
        secondary_completed = (
            "<a:cuscheck:534740177147396097>"
            if progress.get(secondary[0], 0) >= secondary[1]
            else "<a:cuscross:529192535642603530>"
        )

        e = discord.Embed(title="Today's missions", color=0xFFB6C1)
        e.add_field(
            name="Primary Mission",
            value=primary_text.format(x=primary[1], done=progress.get(primary[0], 0)),
        )
        e.add_field(
            name="Secondary Mission",
            value=secondary_text.format(
                x=secondary[1], done=progress.get(secondary[0], 0)
            ),
        )
        e.add_field(
            name="Claimed",
            value=(
                "**Rewards Not claimed**"
                if progress.get("collected", False) == False
                else "**Rewards Claimed**"
            ),
        )
        e.set_footer(text="Missions reset daily")
        await ctx.send(embed=e)

    @missions.command(name="claim")
    async def mission_claim(self, ctx):
        """Claim a mission"""
        user = await ctx.bot.mongo_find(
            "users",
            {"user": ctx.author.id},
            default={"user": ctx.author.id, "progress": {}},
        )
        primary, secondary = (await ctx.bot.db[1].missions.find_one())["missions"]
        progress = user["progress"]

        if (
            progress.get(primary[0], 0) >= primary[1]
            and progress.get(secondary[0], 0) >= secondary[1]
        ):
            async with ctx.bot.db[0].acquire() as pconn:
                user = await ctx.bot.mongo_find(
                    "users",
                    {"user": ctx.author.id},
                    default={"user": ctx.author.id, "progress": {}},
                )
                progress = user["progress"]
                if progress.get("collected", False) == True:
                    await ctx.send(
                        "**You have already claimed rewards for today!\nPlease wait till missions reset.**"
                    )
                else:
                    reward = random.choices(
                        ("chest", "credits", "redeem"),
                        weights=(0.25, 0.50, 0.25),
                    )[0]

                    if reward == "chest":
                        chest_type = random.choice(("common_chest", "rare_chest"))
                        await pconn.execute(
                            f"UPDATE account_bound SET {chest_type} = {chest_type} + 1 WHERE u_id = $1",
                            ctx.author.id,
                        )
                        msg = f"You have claimed a {chest_type}!"
                    elif reward == "redeem":
                        count = random.randint(1, 3)
                        await pconn.execute(
                            "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                            count,
                            ctx.author.id,
                        )
                        msg = f"You have claimed {count} redeems!"
                    elif reward == "credits":
                        count = random.randint(10000, 50000)
                        await pconn.execute(
                            "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                            count,
                            ctx.author.id,
                        )
                        msg = f"You have claimed {count} credits!"
                    progress.update({"collected": True})
                    await ctx.bot.mongo_update(
                        "users", {"user": ctx.author.id}, {"progress": progress}
                    )
                    await ctx.send(embed=make_embed(title=f"Congratulations!\n{msg}"))
        else:
            await ctx.send("Today's missions have not been completed!")


async def setup(bot):
    await bot.add_cog(Missions(bot))
