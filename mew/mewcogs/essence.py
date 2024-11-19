import asyncio
import discord
from discord.ext import commands
from mewutils.checks import check_owner, check_mod
from mewcogs.json_files import make_embed
from mewcogs.pokemon_list import (
    LegendList,
    pseudoList,
    ubList,
    starterList,
)


class Essence(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @check_mod()
    @commands.hybrid_group()
    async def essence(self, ctx):
        ...

    # @check_mod()
    @essence.command(name="craft")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def essence_craft(self, ctx: commands.Context, poke_num: int):
        """Trade-in shiny starter/pseudo/ub/legends for essence."""
        # if ctx.author.id not in (
        # 861318943120818206, #Beto
        # 334155028170407949,
        # 366319068476866570
        # ):
        # await ctx.send("Temporarily unavailable")
        # return

        e = make_embed(
            title="Crafting...",
            description=f"Attempting to trade-in Pokémon for essence!",
        )
        e.set_thumbnail(
            url="https://www.themarysue.com/wp-content/uploads/2022/08/Terastal-Pokemon.jpeg"
        )
        msg = await ctx.send(embed=e)

        await asyncio.sleep(2)

        async with ctx.bot.db[0].acquire() as pconn:
            records = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = (SELECT pokes[$1] FROM users WHERE u_id = $2)",
                poke_num,
                ctx.author.id,
            )

        if not records:
            await msg.edit(
                embed=make_embed(
                    title="Invalid Pokémon",
                    description=f"You don't have that Pokémon!",
                )
            )
            return
        name = records["pokname"]
        poke_id = records["id"]

        # TODO:
        # Remove this once the bot restarts and pokemon_list is updated
        if name in ("Archaludon", "Hydrapple", "Dipplin", "Poltchageist", "Sinistcha"):
            await ctx.send("That is not a valid Pokemon")
            return

        # Embed fun
        if name == "Egg" or name == "egg":
            e.title = "Uh Oh"
            e.description = "Found an Egg, it should be hatched first!"
            await msg.edit(embed=e)
            return
        else:
            e.title = "Still Crafting..."
            e.description = f"Found a {name} !"
        await msg.add_reaction("<a:mewspin:998520051432968273>")
        await asyncio.sleep(1)
        await msg.edit(embed=e)

        # message = await ctx.send(embed=embed, view=view)

        await asyncio.sleep(3)

        form_info = await ctx.bot.db[1].forms.find_one({"identifier": name.lower()})
        ptypes = await ctx.bot.db[1].ptypes.find_one({"id": form_info["pokemon_id"]})

        if not records["shiny"] or records["fav"] or (15 in ptypes["types"]):
            await msg.edit(
                embed=make_embed(
                    title="Invalid Pokémon",
                    description=f"You Pokémon must be a shiny :star2:, not be an Ice-type and not favourited for crafting!",
                )
            )
            return

        if name in starterList:
            async with ctx.bot.db[0].acquire() as pconn:
                maxed = await pconn.fetchval(
                    "SELECT (essence).x >= 25 FROM users WHERE u_id = $1", ctx.author.id
                )
                if maxed:
                    await msg.edit(
                        embed=make_embed(
                            title="Maxed X-Essence",
                            description=f"You have the maximum amount of X-Essence needed for crystallization!",
                        )
                    )
                    return
                await pconn.execute(
                    "UPDATE users SET essence.x = (essence).x + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                e.title = f"Crafted 1 X-Essence from your Shiny {name}"
                e.description = "You are one step closer to Crystallization!"
                await msg.edit(embed=e)
                await ctx.bot.commondb.remove_poke(ctx.author.id, poke_id, delete=True)

        elif name in LegendList or name in pseudoList or name in ubList:
            async with ctx.bot.db[0].acquire() as pconn:
                maxed = await pconn.fetchval(
                    "SELECT (essence).y >= 50 FROM users WHERE u_id = $1", ctx.author.id
                )
                if maxed:
                    await msg.edit(
                        embed=make_embed(
                            title="Maxed Y-Essence",
                            description=f"You have the maximum amount of Y-Essence needed for crystallization!",
                        )
                    )
                    return

            async def button1_callback(interaction: discord.Interaction):
                if interaction.user == ctx.author:
                    async with ctx.bot.db[0].acquire() as pconn:
                        await pconn.execute(
                            "UPDATE users SET essence.x = (essence).x + 1 WHERE u_id = $1",
                            ctx.author.id,
                        )
                    await ctx.bot.commondb.remove_poke(
                        ctx.author.id, poke_id, delete=True
                    )
                    e.title = f"Crafted 1 X-Essence from your :star2: {name}"
                    e.description = "You are one step closer to Crystallization!"
                    await msg.edit(embed=e, view=None)
                    await msg.add_reaction("<a:mewspin:998520051432968273>")

            async def button2_callback(interaction: discord.Interaction):
                if interaction.user == ctx.author:
                    async with ctx.bot.db[0].acquire() as pconn:
                        await pconn.execute(
                            "UPDATE users SET essence.y = (essence).y + 1 WHERE u_id = $1",
                            ctx.author.id,
                        )
                    await ctx.bot.commondb.remove_poke(
                        ctx.author.id, poke_id, delete=True
                    )
                    e.title = f"Crafted 1 Y-Essence from your :star2: {name}"
                    e.description = "You are one step closer to Crystallization!"
                    await msg.edit(embed=e, view=None)
                    await msg.add_reaction("<a:mewspin:998520051432968273>")

            button1 = discord.ui.Button(label="Craft X-Essence?", custom_id="button1")
            button1.callback = button1_callback

            button2 = discord.ui.Button(label="Craft Y-Essence?", custom_id="button2")
            button2.callback = button2_callback

            view = discord.ui.View(timeout=15)
            view.add_item(button1)
            view.add_item(button2)
            await msg.edit(embed=e, view=view)

            interaction: discord.Interaction = await ctx.bot.wait_for(
                "button_click",
                check=lambda i: i.message.id == msg.id and i.user.id == ctx.author.id,
            )

            if interaction.custom_id == "button1":
                button1.disabled = True
                await interaction.response.send_message("Button 1 was clicked")
            elif interaction.custom_id == "button2":
                button2.disabled = True
                await interaction.response.send_message("Button 2 was clicked")

        else:
            await msg.edit(
                embed=make_embed(
                    title="Invalid Pokemon.",
                    description=f"This Pokémon can not be traded-in for essence!",
                )
            )
            return


async def setup(bot):
    await bot.add_cog(Essence(bot))
