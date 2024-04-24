import discord
import asyncpg
import asyncio
import math
import random
import time
import locale

from discord.ext import commands
from datetime import datetime, timedelta

from mewcogs.pokemon_list import berryList
from mewutils.misc import ConfirmView
from mewutils.checks import tradelock


UNSELLABLE = [
    "coin_case",
    "daycare_space",
    "market_space",
    "gleam gem",
    "legend",
    "mythic",
    "rare",
    "common",
    "iv_multiplier",
    "nature_capsule",
    "shiny_multiplier",
    "battle_multiplier",
    "breeding_multiplier",
    "honey",
    "ultranecronium_z",
    "adamant_orb",
    "shadow_stone",
]


class Sell(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def sell(self, ctx):
        """
        Sell commands.
        """
        pass

    # Only using shop items to start
    @sell.command(name="item")
    async def sell_item(self, ctx, item_name: str, amount_sold: int = 1):
        """Sells an item"""
        if amount_sold < 1:
            await ctx.send("You cannot sell less than 1 of an item!")
            return
        item_name = item_name.replace(" ", "_").lower()
        if item_name in UNSELLABLE:
            await ctx.send(f"`{item_name}` can't be sold.")
            return

        item = await ctx.bot.db[1].new_shop.find_one({"item": item_name})

        if item_name in berryList:
            shop_price = 7500
        else:
            if item is None:
                await ctx.send(f"`{item_name}` isn't a valid item.")
                return
            shop_price = item["price"]

        fancy_name = item_name.replace("_", " ")

        # Pull their current bag and process sell
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchrow(
                "SELECT * FROM bag WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send("You have not started!\nStart with `/start` first!")
                return
            inventory = dict(inventory)

            # Check if they even have it
            if inventory[item_name] < amount_sold:
                await ctx.send(f"You don't have enough `{item_name}`s!")
                return

            credits_gained = round((shop_price * 0.65) * amount_sold)

            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                credits_gained,
                ctx.author.id,
            )
        await ctx.bot.commondb.remove_bag_item(
            ctx.author.id, item_name, amount_sold, False
        )
        await ctx.bot.get_partial_messageable(1104056398125465630).send(
            f"__**Sell Item Command Transaction**__\n\N{SMALL BLUE DIAMOND}- {ctx.author.name} - ``{ctx.author.id}`` has sold\n`{amount_sold}x {fancy_name}` for `{credits_gained:,}`\n"
        )

        await ctx.send(
            f"You have successfully sold `{amount_sold}x {fancy_name}` for {credits_gained:,} credits!"
        )

    @sell.command(name="egg")
    @discord.app_commands.describe(
        egg_ids="A valid pokemon number or list of pokemon numbers (separated by space)."
    )
    @tradelock
    async def sell_egg(self, ctx, egg_ids: str):
        """Sells an egg"""
        egg_id = None
        sell_ids = []
        async with ctx.bot.db[0].acquire() as pconn:
            if egg_ids in ("newest", "new", "latest"):
                egg_id = await pconn.fetchval(
                    "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                egg_nums = [egg_id]
            else:
                try:
                    egg_nums = [int(egg_ids)]
                except ValueError:
                    try:
                        egg_nums = [int(x) for x in egg_ids.split(" ")]
                        if len(egg_nums) > 15:
                            await ctx.send(
                                "You can only sell a max of 15 eggs at once."
                            )
                            return
                    except:
                        await ctx.send(
                            "That isn't a valid pokemon number or list of pokemon numbers (separated by space)."
                        )
                        return

            # Sort the eggs in descending order to account for ID shift
            egg_nums.sort(reverse=True)
            egg_count = 0
            total_credits_gained = 0
            previous_id = 0

            for egg_num in egg_nums:
                if egg_num <= 1:
                    await ctx.send("That isn't a valid pokemon number.")
                    return
                # Check for num entered
                if not egg_id:
                    egg_id = await pconn.fetchval(
                        "SELECT pokes[$1] FROM users WHERE u_id = $2",
                        egg_num,
                        ctx.author.id,
                    )
                    # await ctx.send(f"ID Changed : {egg_id}")
                if egg_id is None:
                    await ctx.send("You do not have that many pokemon.")
                    return
                if egg_id == previous_id:
                    await ctx.send(
                        "Duplicate ID found , check your list and try again!"
                    )
                    return

                # Add check for eggs under 100 step count
                data = await pconn.fetchrow(
                    "SELECT counter, pokname, name, fav, COALESCE(hpiv, 0) + COALESCE(atkiv, 0) + COALESCE(spatkiv, 0) + COALESCE(defiv, 0) + COALESCE(spdefiv, 0) + COALESCE(speediv, 0) as ivs FROM pokes WHERE id = $1",
                    egg_id,
                )
                if data is None:
                    await ctx.send("That pokemon doesn't exist.")
                    return

                # Divide data
                step_count = data["counter"]
                name = data["pokname"]
                iv_total = data["ivs"]
                fav = data["fav"]
                becomes = data["name"]

                if name != "Egg":
                    await ctx.send(f"That's a {name}, not an egg!")
                    return
                if step_count < 70:
                    # if ctx.author.id == 334155028170407949:
                    # pass
                    # else:
                    # await ctx.send(
                    # "That egg is too close to hatching, go hatch it instead!"
                    # )
                    # return
                    await ctx.send(
                        "That egg is too close to hatching, go hatch it instead!"
                    )
                    return
                if fav:
                    await ctx.send("That egg is favorited! Unfavorite it first.")
                    return
                if becomes == "Magikarp":
                    await ctx.send(
                        "You cannot sell an egg that will hatch into Magikarp!"
                    )
                    return

                # Passed checks so total IV and calc credits gained
                if iv_total <= 111:
                    credits_gained = 1000
                elif iv_total <= 149:
                    credits_gained = 2000
                elif iv_total <= 176:
                    credits_gained = 3000
                else:
                    credits_gained = 10000
                egg_count += 1
                total_credits_gained += credits_gained

                # Need to set this to None so it grabs the next egg's ID
                sell_ids.append(egg_id)
                previous_id = egg_id
                egg_id = None

            # Have check if eggs are sellable and calculated total
            if not await ConfirmView(
                ctx,
                f"Are you sure you want to sell {egg_count}x Eggs for a Total {total_credits_gained:,}x Credits?",
            ).wait():
                await ctx.send("Sale Canceled")
                return

            # Give credits to user
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $2 WHERE u_id = $1",
                ctx.author.id,
                total_credits_gained,
            )

            # Loop through eggs again
            for egg_num in sell_ids:
                if not egg_id:
                    egg_id = await pconn.fetchval(
                        "SELECT pokes[$1] FROM users WHERE u_id = $2",
                        egg_num,
                        ctx.author.id,
                    )

                await ctx.bot.commondb.remove_poke(ctx.author.id, egg_num)
                egg_id = None

            await ctx.bot.get_partial_messageable(1104056398125465630).send(
                f"__**Sell Eggs Transaction**__\n\N{SMALL BLUE DIAMOND}- {ctx.author.name} - ``{ctx.author.id}`` has sold\n`{egg_count}x {total_credits_gained:,}`\nSold Egg IDs: `{sell_ids}`\n"
            )

            await ctx.send(
                f"Successfully sold {egg_count}x Eggs for a Total of {total_credits_gained:,}x Credits."
            )


async def setup(bot):
    await bot.add_cog(Sell(bot))
