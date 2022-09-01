import discord
import random
from discord.ext import commands

from mewcogs.pokemon_list import *
from mewcogs.json_files import *
from mewutils.checks import tradelock
from typing import Literal


multiplier_max = {"battle-multiplier": 50, "shiny-multiplier": 50}

def get_perks(plan):
    dets = {}
    if plan == "regular":
        dets["nature-capsules"] = 2
        dets["battle-multiplier"] = 0
        dets["shiny-multiplier"] = 0
        dets["daycare-limit"] = 3
        dets["coin-case"] = 150000
        dets["price"] = 5
    elif plan == "gold":
        dets["nature-capsules"] = 5
        dets["honey"] = 5
        dets["battle-multiplier"] = 1
        dets["shiny-multiplier"] = 2
        dets["daycare-limit"] = 6
        dets["coin-case"] = 300000
        dets["price"] = 10
    elif plan == "platinum":
        dets["nature-capsules"] = 7
        dets["honey"] = 10
        dets["battle-multiplier"] = 4
        dets["shiny-multiplier"] = 6
        dets["daycare-limit"] = 9
        dets["coin-case"] = 600000
        dets["price"] = 25
    elif plan == "diamond":
        dets["nature-capsules"] = 15
        dets["honey"] = 25
        dets["battle-multiplier"] = 10
        dets["shiny-multiplier"] = 10
        dets["daycare-limit"] = 15
        dets["coin-case"] = 800000
        dets["price"] = 50
    elif plan == "worth too much":
        dets["nature-capsules"] = 30
        dets["honey"] = 40
        dets["battle-multiplier"] = 30
        dets["shiny-multiplier"] = 10
        dets["daycare-limit"] = 20
        dets["coin-case"] = 2000000
        dets["ultranecronium-z"] = 1
        dets["bike"] = 1
        dets["price"] = 150
    return dets


def get_descrip(item):
    return {
        "nature-capsules": "Use Nature Capsules to change your Pokemon's Nature",
        "honey": "Honey Increases your chance of spawning a Legendary while talking in a Server",
        "battle-multiplier": "Battle Multipliers Multiply all Reward from a battle or duel such as happiness, credits and experience",
        "shiny-multiplier": "Shiny Multipliers Increase your chance of Redeeming or Spawning a shiny while talking in a Server",
        "daycare-limit": "Daycare Limit increases the amount of Offspring you can breed at a time!",
        "coin-case": "Get Coins to Use and Play the Slots in the Game corner!",
        "ultranecronium-z": "Transform Necrozma to it's Ultra form",
        "bike": ":bike: Speed up egg hatching by 2x",
    }.get(item)


class Redeem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CREDITS_PER_MULTI = 125000

    @commands.hybrid_command()
    async def packs(self, ctx):
        """View all redeemable packs."""
        packs = ["regular", "gold", "platinum", "diamond", "worth too much"]
        for idx, pack in enumerate(packs, start=1):
            e = discord.Embed(title=f"{pack.capitalize()} Pack", color=0xFFB6C1)
            s = get_perks(pack)
            price = s["price"]
            s.pop("price", None)
            e.description = f"Price - {price} Redeems\nPack ID - {idx} Buy this pack with `/redeem pack {idx}`\nIn this pack you get these: "
            for thing in s:
                desc = get_descrip(thing)
                n_thing = thing.replace("-", " ").capitalize()
                n_thing = (
                    "Honey (Increased Legendary encounter chance)"
                    if "Honey" in n_thing
                    else n_thing
                )
                e.add_field(
                    name=n_thing.replace("multiplier", "chance")
                    if "Shiny" in n_thing
                    else n_thing,
                    value=f"{s[thing]}{'%' if 'shiny' in thing or 'honey' in thing else 'x'}\n{desc}",
                    inline=False,
                )
            e.set_footer(text="Shiny Chance and Honey have a Max of 50")
            try:
                await ctx.author.send(embed=e)
            except discord.HTTPException:
                await ctx.send("I could not DM you the Pack information!")
                return
        await ctx.send("All available Packs and their information has been sent to DMs!")

    @commands.hybrid_group()
    async def redeem(self, ctx):
        ...

    @redeem.command(name="shop")
    async def redeem_shop(self, ctx):
        """View some possible items you can spend your redeems on!"""
        async with ctx.bot.db[0].acquire() as pconn:
            redeems = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = $1", ctx.author.id
            )
            if redeems is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
    
        e = discord.Embed(title="Redeem Shop", color=ctx.bot.get_random_color())
        e.description = (
            f"You have {redeems} Redeems, get more with `/donate` or `/vote`"
        )
        e.add_field(
            name="Pokemon | 1 Redeem",
            value=f"`/redeem <pokemon_name> | Redeem any Pokemon of your choice`",
            inline=False,
        )
        # e.add_field(name="Redeem multiple!", value="Redeem any Amount of Pokemon with `{}redeemmultiple <amount> <pokemon_name>` or redeem multiple credits using `{ctx.prefix}redeemmultiple credits <amount_of_redeem_to_use>`")
        e.add_field(
            name="Credits | 1 Redeem = 50,000 Credits",
            value=f"`/redeem credits | Redeem 50,000 credits`",
            inline=False,
        )
        e.add_field(
            name="Nature capsules | 1 Redeem = 5 Nature Capsules",
            value=f"`/redeem nature capsules | Use nature capsules to edit Pokemon nature.`",
            inline=False,
        )
        e.add_field(
            name="Honey | 5 Redeems = 1 Honey",
            value=f"`/redeem honey | /spread honey <amount> | Redeem and Spread honey on a channel`",
            inline=False,
        )
        # e.add_field(name="Packs", value="Get Extra Features, Items with `{ctx.prefix}packs`\nRedeem a pack with `{ctx.prefix}redeem pack <pack_id>`")
        e.add_field(
            name="EV points | 1 Redeem = 255 EVs",
            value=f"`/redeem evs | Redeem 255 EV points`",
            inline=False,
        )
        e.add_field(
            name="30 Redeems = 1 Random Shiny",
            value=f"`/redeem shiny | Redeem random Shiny Legendary, Mythical, or Common Pokemon`",
            inline=False,
        )
        e.add_field(
            name="Bike | 100 Redeems = 1 Bike",
            value=f"`/redeem bike | Redeem a bike and double egg hatching rate`",
            inline=False,
        )
        e.add_field(
            name="Packs",
            value=f"`/packs | Get extra bundles, features, items from packs`",
        )
        await ctx.send(embed=e)
        return
    
    @tradelock
    @redeem.command()
    @discord.app_commands.describe(pack="The ID of the pack you want to redeem. View available packs with `/packs`.")
    async def pack(self, ctx, pack: Literal[1, 2, 3, 4, 5]):
        """Spend your redeems a pack to get extra perks, bundles, features & items"""
        if pack == 1:
            perk = "regular"
        elif pack == 2:
            perk = "gold"
        elif pack == 3:
            perk = "platinum"
        elif pack == 4:
            perk = "diamond"
        elif pack == 5:
            perk = "worth too much"
        pack = get_perks(perk)
        price = pack["price"]
        async with ctx.bot.db[0].acquire() as pconn:
            redeems = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if redeems < price:
                await ctx.send(
                    f"You cannot afford the {price} redeem it would cost to purchase that pack!"
                )
                return
            await pconn.execute(
                "UPDATE users SET redeems = redeems - $1 where u_id = $2",
                price,
                ctx.author.id,
            )
        daycarelimit = pack["daycare-limit"]
        pack.pop("price", None)
        pack.pop("daycare-limit", None)
        async with ctx.bot.db[0].acquire() as pconn:
            current_inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            current_items = await pconn.fetchval(
                "SELECT items::json FROM users WHERE u_id = $1", ctx.author.id
            )
        # current_inv.pop('coin-case', None) if 'coin-case' in current_inv else None
        extra_creds = 0
        for item in pack:
            try:
                if item.endswith("-z"):
                    current_items[item] = current_items.get(item, 0) + 1
                    async with ctx.bot.db[0].acquire() as pconn:
                        await pconn.execute(
                            "UPDATE users SET items = $1::json where u_id = $2",
                            current_items,
                            ctx.author.id,
                        )
                elif item == "bike":
                    async with ctx.bot.db[0].acquire() as pconn:
                        await pconn.execute(
                            "UPDATE users SET bike = $2 where u_id = $1",
                            ctx.author.id,
                            True,
                        )
                else:
                    extra = max(0, (current_inv.get(item, 0) + pack[item]) - (multiplier_max.get(item, 9999999999999999999999999)))
                    extra_creds += extra * self.CREDITS_PER_MULTI
                    current_inv[item] = min(
                        current_inv.get(item, 0) + pack[item], multiplier_max.get(item, 9999999999999999999999999)
                    )
            except:
                continue
        async with ctx.bot.db[0].acquire() as pconn:
            try:
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json, daycarelimit = daycarelimit + $3, mewcoins = mewcoins + $4 WHERE u_id = $2",
                    current_inv,
                    ctx.author.id,
                    daycarelimit,
                    extra_creds,
                )
            except Exception as e:
                raise e
                await ctx.send(
                    "You do not have enough Redeems or you have stacked up your perks to the limit!"
                )
                return

        e = discord.Embed(title=f"{perk.capitalize()} Pack", color=0xFFB6C1)
        e.description = "You have Successfully purchased these: "
        for item in pack:
            n_thing = item.replace("-", " ").capitalize()
            n_thing = (
                "Honey (Increased Legendary encounter chance)"
                if "Honey" in n_thing
                else n_thing
            )
            e.add_field(
                name=n_thing.replace("multiplier", "chance")
                if "Shiny" in n_thing
                else n_thing,
                value=f"{pack[item]}{'%' if 'shiny' in item or 'honey' in item else 'x'}",
                inline=False,
            )
        if extra_creds:
            e.add_field(
                name="Credits",
                value=f"{extra_creds}",
                inline=False,
            )
        await ctx.send(embed=e)
    
    @tradelock
    @redeem.command()
    async def shiny(self, ctx):
        """Spend your redeems for a random shiny."""
        e = discord.Embed(color=ctx.bot.get_random_color())
        shiny = random.choice(totalList)
        async with ctx.bot.db[0].acquire() as pconn:
            redeems = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = $1", ctx.author.id
            )
            if redeems is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if redeems < 30:
                await ctx.send("You don't have 30 Redeems!")
                return
            await pconn.execute(
                "UPDATE users SET redeems = redeems - 30 WHERE u_id = $1",
                ctx.author.id,
            )
        pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, shiny, shiny=True)
        ivpercent = round((pokedata.iv_sum / 186) * 100, 2)
        await ctx.bot.get_partial_messageable(998341289164689459).send(f"``User:`` {ctx.author} | ``ID:`` {ctx.author.id}\nHas redeemed a random shiny {shiny} (`{pokedata.id}`)\n----------------------------------")
        e.add_field(name="Random Shiny", value=f"{shiny} ({ivpercent}% iv)", inline=False)
        await ctx.send(embed=e)
    
    @tradelock
    @redeem.command()
    async def bike(self, ctx):
        """Spend your redeems for a bike."""
        e = discord.Embed(color=ctx.bot.get_random_color())
        async with ctx.bot.db[0].acquire() as pconn:
            redeems = await pconn.fetchval(
                "SELECT redeems FROM users WHERE u_id = $1", ctx.author.id
            )
            if redeems < 100:
                await ctx.send("You do not have enough redeems")
                return

            await pconn.execute(
                "UPDATE users SET bike = $2, redeems = redeems - 100 where u_id = $1",
                ctx.author.id,
                True,
            )
        e.description = "You have Successfully purchased a :bike:"
        await ctx.send(embed=e)

    @tradelock
    @redeem.command(aliases=["coins"])
    async def credits(self, ctx):
        """Trade 1 redeem for 50,000 credits."""
        async with ctx.bot.db[0].acquire() as pconn:
            redeems = await pconn.fetchval(
                    "SELECT redeems FROM users WHERE u_id = $1", ctx.author.id
                )
            try:
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 50000, redeems = redeems - 1 Where u_id = $1",
                    ctx.author.id,
                )
            except:
                await ctx.send("You do not have enough redeems")
                return
            await ctx.send("50,000 Has been credited to your balance!")

    @tradelock
    @redeem.command()
    async def honey(self, ctx):
        """Spend your redeems and get honey | Can be spread on a channel to attract rare & shiny Pokemon."""
        async with ctx.bot.db[0].acquire() as pconn:
            inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            inv["honey"] = inv.get("honey", 0) + 1
            try:
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json, redeems = redeems - 5 WHERE u_id = $2",
                    inv,
                    ctx.author.id,
                )
            except:
                await ctx.send("You do not have enough redeems")
                return
            await ctx.send("You redeemed 1x honey!")
    
    @tradelock
    @redeem.command()
    async def evs(self, ctx):
        """Redeem 255 EV points."""
        async with ctx.bot.db[0].acquire() as pconn:
            try:
                await pconn.execute(
                    "UPDATE users SET evpoints = evpoints + 255, redeems = redeems - 1 WHERE u_id = $1",
                    ctx.author.id,
                )
            except:
                await ctx.send("You do not have enough redeems")
                return
            await ctx.send(
                "You now have 255 Effort Value Points!\nSee them on your Trainer Card!"
            )
    
    @tradelock
    @redeem.group()
    async def nature(self, ctx):
        ...

    @nature.command()
    async def capsules(self, ctx):
        """Redeem 5 nature capsules"""
        async with ctx.bot.db[0].acquire() as pconn:
            inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            inv["nature-capsules"] = inv.get("nature-capsules", 0) + 5
            try:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems - 1, inventory = $1::json WHERE u_id = $2",
                    inv,
                    ctx.author.id,
                )
            except:
                await ctx.send("You do not have enough redeems")
                return
            await ctx.send("You have Successfully purchased 5 Nature Capsules")

    @tradelock
    @discord.app_commands.describe(pokemon="The Pokemon you want to redeem.")
    @redeem.command(with_app_command=True) # This has to be registered
    async def pokemon(self, ctx, pokemon: str):
        """Redeem a specific Pokemon"""
        pokemon = pokemon.capitalize().replace(" ", "-")
        if not pokemon in totalList:
            await ctx.send("That Pokemon does not exist!\nView the redeem shop with `/redeem`")
            return
        threshold = 4000
        async with ctx.bot.db[0].acquire() as pconn:
            inventory, items, redeems = await pconn.fetchrow(
                "SELECT inventory::json, items::json, redeems FROM users WHERE u_id = $1",
                ctx.author.id,
            )

        threshold = round(threshold - threshold * (inventory["shiny-multiplier"] / 100))
        shiny = random.choice([False for i in range(threshold)] + [True])

        if redeems < 1:
            await ctx.send("You do not have enough redeems")
            return
        item = None
        async with ctx.bot.db[0].acquire() as pconn:
            if (
                max(1, int(random.random() * 30)) == max(1, int(random.random() * 30))
                and pokemon.lower() in REDEEM_DROPS
            ):
                item = REDEEM_DROPS[pokemon.lower()]
                items[item] = items.get(item, 0) + 1
            await pconn.execute(
                "UPDATE users SET redeems = redeems - 1, items = $1::json, inventory = $2::json WHERE u_id = $3",
                items,
                inventory,
                ctx.author.id,
            )
        pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=shiny)
        ivpercent = round((pokedata.iv_sum / 186) * 100, 2)
        await ctx.bot.get_partial_messageable(998341289164689459).send(f"``User:`` {ctx.author} | ``ID:`` {ctx.author.id}\nHas redeemed a {pokedata.emoji}{pokemon} (`{pokedata.id}`)\n----------------------------------")
        msg = f"Here's your {pokedata.emoji}{pokemon} ({ivpercent}% iv)!\n"
        if item:
            msg += f"Dropped - {item}"
        await ctx.send(msg)
        user = await ctx.bot.mongo_find(
            "users",
            {"user": ctx.author.id},
            default={"user": ctx.author.id, "progress": {}},
        )
        progress = user["progress"]
        progress["redeem"] = progress.get("redeem", 0) + 1
        await ctx.bot.mongo_update("users", {"user": ctx.author.id}, {"progress": progress})

    @redeem.command(with_app_command=True) # This has to be registered
    @discord.app_commands.describe(option="Either Credits or a Pokemon")
    @tradelock
    async def multiple(self, ctx, amount: int, option: str):
        """Redeem multiple Pokemon or Credits"""
        if option == "credits":
            async with ctx.bot.db[0].acquire() as pconn:
                redeems = await pconn.fetchval(
                    "SELECT redeems FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                if redeems < amount:
                    await ctx.send("You do not have enough redeems")
                    return
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + (50000 * $1), redeems = redeems - $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            await ctx.bot.get_partial_messageable(998341289164689459).send(f"``User:`` {ctx.author} | ``ID:`` {ctx.author.id}\nHas redeemed {amount} redeems for {50000*amount:,} credits!\n----------------------------------")
            await ctx.send(f"You redeemed {amount} redeems for {50000*amount:,} credits!")
            return
        # Option is probably a pokemon name
        pokemon = option
        if not pokemon.capitalize().replace(" ", "-") in totalList:
            await ctx.send("That's not a valid pokemon name!")
            return
        pokemon = pokemon.capitalize().replace(" ", "-")
        threshold = 4000
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT inventory::json, items::json, redeems FROM users WHERE u_id = $1",
                ctx.author.id,
            )
        if details is None:
            await ctx.send("You have not started!\nStart with `/start` first.")
            return
        inventory, items, redeems = details
        threshold = round(threshold - threshold * (inventory["shiny-multiplier"] / 100))

        if redeems < amount:
            await ctx.send(f"You do not have enough redeems")
            return
        else:
            await ctx.bot.get_partial_messageable(998341289164689459).send(f"``User:`` {ctx.author} | ``ID:`` {ctx.author.id}\nHas redeemed {amount} {pokemon} with redeemmultiple!\n----------------------------------")
            await ctx.send(f"Redeeming {amount} {pokemon}...")
            async with ctx.bot.db[0].acquire() as pconn:
                for i in range(amount):
                    item = None
                    if not random.randrange(30) and pokemon.lower() in REDEEM_DROPS:
                        item = REDEEM_DROPS[pokemon.lower()]
                        items[item] = items.get(item, 0) + 1
                    await pconn.execute(
                        "UPDATE users SET redeems = redeems - 1, items = $1::json, inventory = $2::json WHERE u_id = $3",
                        items,
                        inventory,
                        ctx.author.id,
                    )
                    shiny = not random.randrange(threshold)
                    pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=shiny)
                    await ctx.bot.get_partial_messageable(998341289164689459).send(f"``User:`` {ctx.author} | ``ID:`` {ctx.author.id}\nHas redeemed a {pokedata.emoji}{pokemon} (`{pokedata.id}`) with redeem-multiple command.\n----------------------------------")
                    #
                    user = await ctx.bot.mongo_find(
                        "users",
                        {"user": ctx.author.id},
                        default={"user": ctx.author.id, "progress": {}},
                    )
                    progress = user["progress"]
                    progress["redeem"] = progress.get("redeem", 0) + 1
                    await ctx.bot.mongo_update(
                        "users", {"user": ctx.author.id}, {"progress": progress}
                    )
                    #
                    if item:
                        await ctx.send(f"Dropped - {item}")
            await ctx.send(f"Successfully redeemed {amount} {pokemon}!")


async def setup(bot):
    await bot.add_cog(Redeem(bot))