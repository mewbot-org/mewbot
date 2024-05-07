from typing import Literal
import discord
import asyncpg
from discord.ext import commands
import asyncio
import random
import time
from datetime import datetime, timedelta


from mewcogs.json_files import *
from mewcogs.pokemon_list import is_formed, berryList
from pokemon_utils.utils import evolve
from mewcogs.market import MAX_MARKET_SLOTS
from mewutils.misc import ConfirmView
from typing import Literal

#Only placed used so moved from pokemon_list
activeItemList = (
    "tart_apple",
    "sweet_apple",
    "dusk_stone",
    "thunder_stone",
    "fire_stone",
    "water_stone",
    "dawn_stone",
    "leaf_stone",
    "moon_stone",
    "shiny_stone",
    "evo_stone",
    "cracked_pot",
    "chipped_pot",
    "meltan_candy",
    "galarica_wreath",
    "galarica_cuff",
    "black_augurite",
    "peat_block",
    "metal_alloy",
    "sun_stone",
    "syrupy_apple",
    "ice_stone",
)

bagItemList = (
    "aguav_seed",
    "figy_seed",
    "iapapa_seed",
    "mago_seed",
    "wiki_seed",
    "sitrus_seed",
    "apicot_seed",
    "ganlon_seed",
    "lansat_seed",
    "liechi_seed",
    "micle_seed",
    "petaya_seed",
    "salac_seed",
    "starf_seed",
    "aspear_seed",
    "cheri_seed",
    "chesto_seed",
    "lum_seed",
    "pecha_seed",
    "persim_seed",
    "rawst_seed",
    "water_tank",
    "fertilizer",
)


class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize())

    async def initialize(self):
        # This is to make sure the dict exists before we access in the cog check
        await self.bot.redis_manager.redis.execute(
            "HMSET", "energycooldown", "examplekey", "examplevalue"
        )

    @staticmethod
    async def prep_item_remove(ctx):
        """Handles ensuring a user can unequip an item. Returns None if they cannot, (held_item, pokname) if they can."""
        async with ctx.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT pokes.hitem, pokes.pokname FROM pokes INNER JOIN users ON pokes.id = (SELECT selected FROM users WHERE u_id = $1) AND users.u_id = $1",
                ctx.author.id,
            )
        if data is None:
            await ctx.send(
                "You do not have a pokemon selected!\nSelect one with `/select` first."
            )
            return None
        held_item, name = data
        if held_item in ("None", None, "none"):
            await ctx.send("Your selected Pokemon is not holding any item!")
            return None
        # If dash in held_item this stuff breaks , replace it if it's there
        if "-" in held_item:
            held_item = held_item.replace("-", "_")

        if (
            held_item in ("megastone", "mega_stone", "mega_stone_x", "mega_stone_y")
            and any(name.endswith(x) for x in ("-mega", "-x", "-y"))
            and name.lower() != "rayquaza-mega"
        ):
            await ctx.send(
                f"You must deform this Pokemon before unequipping the {held_item}!"
            )
            return None
        if is_formed(name) and held_item in (
            "primal_orb",
            "blue_orb",
            "red_orb",
            "griseous_orb",
            "ultranecronium_z",
            "rusty_sword",
            "rusty_shield",
            "ultra_toxin",
        ):
            await ctx.send(
                f"You must deform this Pokemon before unequipping the {held_item}!"
            )
            return None
        return (held_item, name)

    @commands.hybrid_group()
    async def items(self, ctx):
        """
        Item commands.
        """
        pass

    @items.command()
    async def unequip(self, ctx):
        """Unequips an item"""
        data = await self.prep_item_remove(ctx)
        if data is None:
            return
        held_item, name = data
        async with ctx.bot.db[0].acquire() as pconn:
            await self.bot.commondb.add_bag_item(
                ctx.author.id, held_item.replace("-", "_"), 1
            )
            await pconn.execute(
                "UPDATE pokes SET hitem = 'None' WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx.author.id,
            )
        await ctx.send(f"Successfully unequipped a {held_item} from selected Pokemon")

    @items.command()
    async def equip(self, ctx, item_name: str):
        """Equips an item"""
        item_name = item_name.replace("-", "_")
        item_name = "_".join(item_name.split()).lower()
        item_info = await ctx.bot.db[1].new_shop.find_one({"item": item_name})

        for item in SHOP:
            if item["item"] == item_name:
                item_info = item

        # Prelimary checks
        if item_name in bagItemList:
            await ctx.send("Sorry, that item is can not be equipped.")
            return
        if item_name == "nature_capsule":
            await ctx.send(
                "Use `/change nature` to use a nature capsule to change your pokemon's nature."
            )
            return
        if not item_name in berryList and not item_info:
            await ctx.send("That Item does not exist!")
            return
        if item_name in activeItemList:
            await ctx.send(
                f"That item cannot be equiped! Use it on your poke with `/apply {item_name}`."
            )
            return

        # Pull player's bag
        async with ctx.bot.db[0].acquire() as conn:
            dets = await conn.fetchrow(
                "SELECT * FROM bag WHERE u_id = $1", ctx.author.id
            )
            dets = dict(dets)
        if (dets[item_name] - 1) < 0:
            await ctx.send(f"You do not have any {item_name}!")
            return

        # Process the item equip
        async with ctx.bot.db[0].acquire() as pconn:
            _id = await pconn.fetchval(
                "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
            )
            data = await pconn.fetchrow(
                "SELECT pokname, hitem FROM pokes WHERE id = $1", _id
            )
            if data is None:
                await ctx.send(
                    "You do not have a pokemon selected!\nSelect one with `/select` first."
                )
                return
            pokename, hitem = data
            if not hitem.lower() == "none":
                await ctx.send(
                    f"Your pokemon is already holding the {hitem}! Unequip it with `/unequip` first!."
                )
                return
            ab_index = await pconn.fetchval(
                "SELECT ability_index FROM pokes WHERE id = $1", _id
            )
            if item_name == "ability_capsule":
                form_info = await ctx.bot.db[1].forms.find_one(
                    {"identifier": pokename.lower()}
                )
                ab_ids = []
                async for ability in ctx.bot.db[1].poke_abilities.find(
                    {"pokemon_id": form_info["pokemon_id"]}
                ):
                    ab_ids.append(ability["ability_id"])

                if len(ab_ids) == 1:
                    await ctx.send("That Pokemon cannot have its ability changed!")
                    return
                try:
                    new_ab = ab_ids[ab_index + 1]
                    new_index = ab_ids.index(new_ab)
                except IndexError:
                    new_index = 0
                await pconn.execute(
                    "UPDATE pokes SET ability_index = $1 WHERE id = $2", new_index, _id
                )
                ab_id = ab_ids[new_index]
                new_ability = await ctx.bot.db[1].abilities.find_one({"id": ab_id})

                await ctx.bot.commondb.remove_bag_item(ctx.author.id, item_name, 1)
                await ctx.send(
                    f"You have Successfully changed your Pokémons ability to {new_ability['identifier']}"
                )
                return
            if item_name == "daycare_space":
                await pconn.execute(
                    "UPDATE users SET daycarelimit = daycarelimit + 1 WHERE u_id = $",
                    ctx.author.id,
                )
                await ctx.bot.commondb.remove_bag_item(ctx.author.id, item_name, 1)
                await ctx.send("You have successfully equipped an Extra Daycare Space!")
                return
            if item_name == "ev_reset":
                await ctx.bot.commondb.remove_bag_item(ctx.author.id, item_name, 1)
                await pconn.execute(
                    "UPDATE pokes SET hpev = 0, atkev = 0, defev = 0, spatkev = 0, spdefev = 0, speedev = 0 WHERE id = $1",
                    _id,
                )
                await ctx.send(
                    "You have successfully reset the Effort Values (EVs) of your selected Pokemon!"
                )
                return
            if "-mega" in pokename and pokename != "Rayquaza-mega":
                await ctx.send(
                    "You can not equip an item for a Mega Pokemon. Use `/deform` to de-mega your Pokemon!"
                )
                return
            if item_name in ("zinc", "hp_up", "protein", "calcium", "iron", "carbos"):
                try:
                    if item_name == "zinc":
                        await pconn.execute(
                            "UPDATE pokes SET spdefev = spdefev + 10 WHERE id = $1", _id
                        )
                    elif item_name == "hp_up":
                        await pconn.execute(
                            "UPDATE pokes SET hpev = hpev + 10 WHERE id = $1", _id
                        )
                    elif item_name == "protein":
                        await pconn.execute(
                            "UPDATE pokes SET atkev = atkev + 10 WHERE id = $1", _id
                        )
                    elif item_name == "calcium":
                        await pconn.execute(
                            "UPDATE pokes SET spatkev = spatkev + 10 WHERE id = $1", _id
                        )
                    elif item_name == "iron":
                        await pconn.execute(
                            "UPDATE pokes SET defev = defev + 10 WHERE id = $1", _id
                        )
                    elif item_name == "carbos":
                        await pconn.execute(
                            "UPDATE pokes SET speedev = speedev + 10 WHERE id = $1", _id
                        )
                    await ctx.bot.commondb.remove_bag_item(ctx.author.id, item_name, 1)
                except:
                    await ctx.send("Your Pokemon has maxed all 510 EVs")
                    return
                await ctx.send(f"You have successfully used your {item_name}")
                return
            if item_name.endswith("_rod"):
                await ctx.bot.db.commondb.remove_bag_item(ctx.author.id, item_name, 1)
                await pconn.execute(
                    "UPDATE users SET held_item = $2 WHERE u_id = $1",
                    ctx.author.id,
                    item_name,
                )
                await ctx.send(f"You have successfully equiped your {item_name}")
                return
            if item_name.endswith("_shovel"):
                await ctx.bot.db.commondb.remove_bag_item(ctx.author.id, item_name, 1)
                await pconn.execute(
                    "UPDATE users SET shovel = $2 WHERE u_id = $1",
                    ctx.author.id,
                    item_name,
                )
                await ctx.send(f"You have successfully equiped your {item_name}")
                return
            name = await pconn.fetchval("SELECT pokname FROM pokes WHERE id = $1", _id)
            await pconn.execute(
                "UPDATE pokes set hitem = $2 WHERE id = $1", _id, item_name
            )
            await self.bot.commondb.remove_bag_item(ctx.author.id, item_name, 1)
            await ctx.send(
                f"You have successfully given your selected Pokemon a {item_name}"
            )
            await evolve(
                ctx,
                ctx.bot,
                dict(await pconn.fetchrow("SELECT * FROM pokes WHERE id = $1", _id)),
                ctx.author,
                channel=ctx.channel,
            )

    @items.command()
    async def drop(self, ctx):
        """Drops an item"""
        data = await self.prep_item_remove(ctx)
        if data is None:
            return
        held_item, name = data
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE pokes SET hitem = $2 WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx.author.id,
                "None",
            )
        await ctx.send(f"Successfully Dropped the {held_item}")

    @items.command()
    async def transfer(self, ctx, pokemon_number: int):
        """Transfers an item"""
        data = await self.prep_item_remove(ctx)
        if data is None:
            return
        held_item, name = data
        async with ctx.bot.db[0].acquire() as pconn:
            poke = await pconn.fetchval(
                "SELECT pokes[$1] FROM users WHERE u_id = $2",
                pokemon_number,
                ctx.author.id,
            )
            if poke is None:
                await ctx.send("You do not have that Pokemon!")
                return
            details = await pconn.fetchrow("SELECT * FROM pokes WHERE id = $1", poke)
            if details["hitem"].capitalize() != "None":
                await ctx.send("That Pokemon is already holding an item")
                return
            pokename = details["pokname"].capitalize()
            await pconn.execute(
                "UPDATE pokes SET hitem = 'None' WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE pokes SET hitem = $1 WHERE id = $2", held_item, poke
            )
        await ctx.send(
            f"You have successfully transfered the {held_item} from your {name} to your {pokename}!"
        )

    @items.command()
    async def apply(self, ctx, item_name: str):
        """Use an active item to evolve a poke."""
        item_name = "_".join(item_name.split()).lower()
        fancy_name = item_name.title()
        # Preliminary checks
        if item_name == "nature_capsule":
            await ctx.send(
                "Use `/change nature` to use a nature capsule to change your pokemon's nature."
            )
            return
        if item_name not in activeItemList:
            await ctx.send(
                f"That item cannot be used on a poke! Try equiping it with `/equip {item_name}`."
            )
            return

        # Pull bag and make sure they have item
        async with ctx.bot.db[0].acquire() as pconn:
            dets = await pconn.fetchrow(
                "SELECT * FROM bag WHERE u_id = $1", ctx.author.id
            )
            dets = dict(dets)

        if dets is None:
            await ctx.send("You have not started!\nStart with `/start first.")
            return
        if dets[item_name] == 0:
            await ctx.send(f"You do not have any {fancy_name}!")
            return

        # Checks are done, proceed
        async with ctx.bot.db[0].acquire() as pconn:
            _id = await pconn.fetchval(
                "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
            )
            poke = await pconn.fetchrow("SELECT * FROM pokes WHERE id = $1", _id)
        if poke is None:
            await ctx.send(
                "You do not have a pokemon selected! Select one with `/select` first."
            )
            return
        evo_result = await evolve(
            ctx,
            ctx.bot,
            dict(poke),
            ctx.author,
            channel=ctx.channel,
            active_item=item_name.replace("_", "-"),
        )
        if evo_result is False or not evo_result.used_active_item():
            await ctx.send(f"The {item_name} had no effect!")
            return
        await ctx.bot.commondb.remove_bag_item(ctx.author.id, item_name, 1)
        await ctx.send(f"Your {fancy_name} was consumed!")

    @commands.hybrid_group()
    async def buy(self, ctx):
        ...

    @buy.command(name="item")
    async def buy_item(self, ctx, item_name: str):
        """Buy an item from the items shop."""
        item_name = item_name.replace(" ", "_").lower()
        fancy_name = item_name.replace("_", " ").lower()

        if item_name == "evo_stone":
            await ctx.send("Purchasing that item is currently disabled.")
            return
        if item_name == "daycare_space":
            await ctx.send("Use `/buy daycare`, not `/buy item daycare-space`.")
            return
        # Check so players can't buy crystals
        if item_name in (
            "sky_crystal",
            "light_crystal",
            "abyss_crystal",
            "internal_crystal",
            "energy_crystal",
        ):
            await ctx.send("You can't buy crystals!")
            return

        item = await ctx.bot.db[1].new_shop.find_one({"item": item_name})
        if item is None:
            await ctx.send("That item is not in the market")
            return

        price = item["price"]

        async with ctx.bot.db[0].acquire() as pconn:
            # items, current_creds = await pconn.fetchrow("SELECT  FROM users WHERE u_id = $1", ctx.author.id)
            data = await pconn.fetchrow(
                "SELECT mewcoins, selected FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if data is None:
                await ctx.send("You have not started!\nStart with `/start` first.")
                return
            current_creds, selected_id = data

            if current_creds < price:
                await ctx.send(f"You don't have {price:,}ℳ")
                return
            
            vat_price = ctx.bot.misc.get_vat_price(price)

            # Market spaces
            if item_name == "market_space":
                if current_creds < 30000:
                    await ctx.send(
                        f"You need 30,000 credits to buy a market space! You only have {current_creds:,}..."
                    )
                    return
                marketlimit = await pconn.fetchval(
                    "SELECT marketlimit FROM users WHERE u_id = $1", ctx.author.id
                )
                if marketlimit >= MAX_MARKET_SLOTS:
                    await ctx.send(
                        "You already have the maximum number of market spaces!"
                    )
                    return
                await pconn.fetchval(
                    "UPDATE users SET marketlimit = marketlimit + 1, mewcoins = mewcoins - $1 WHERE u_id = $2",
                    ctx.bot.misc.get_vat_price(30000),
                    ctx.author.id,
                )
                await ctx.send("You have successfully bought an extra market space!")
                return

            # Fishing rods
            if "_rod" in item_name:
                await pconn.execute(
                    "UPDATE users SET held_item = $1 WHERE u_id = $2",
                    item_name,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $2 WHERE u_id = $1",
                    ctx.author.id,
                    vat_price,
                )
                await ctx.send(
                    f"You have successfully bought the {fancy_name.title()} for {price:,} credits!"
                )
                return
            # Shovels
            if "_shovel" in item_name:
                await pconn.execute(
                    "UPDATE users SET shovel = $1 WHERE u_id = $2",
                    item_name,
                    ctx.author.id,
                )
                vat_price = ctx.bot.misc.get_vat_price(price)
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $2 WHERE u_id = $1",
                    ctx.author.id,
                    vat_price,
                )
                await ctx.send(
                    f"You have successfully bought the {fancy_name.title()} for {price:,} credits!"
                )
                return

            # Active items that go in bag but need different final message
            if item_name in activeItemList:
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                    vat_price,
                    ctx.author.id,
                )
                await ctx.bot.commondb.add_bag_item(ctx.author.id, item_name, 1)
                await ctx.send(
                    f"You have successfully bought a {fancy_name.title()} for {price:,} credits!\nApply it with `/items apply [item]`."
                )
                return

            # Items that should go in user's bag
            if item_name in bagItemList:
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                    vat_price,
                    ctx.author.id,
                )
                if item_name == "water_tank":
                    await pconn.execute(
                        "UPDATE bag SET water_tank = 10 WHERE u_id = $1", ctx.author.id
                    )
                    await ctx.send("Successfully filled your water tank!")
                    return
                if item_name == "fertilizer":
                    await pconn.execute(
                        "UPDATE bag SET fertilizer = fertilizer + 1 WHERE u_id = $1",
                        ctx.author.id,
                    )
                else:
                    await ctx.bot.commondb.add_bag_item(ctx.author.id, item_name, 1)
                await ctx.send(
                    f"You have successfully bought a {fancy_name.title()} for {price:,} credits!"
                )
                return

            if selected_id:
                _id, pokename, ab_index = await pconn.fetchrow(
                    "SELECT id, pokname, ability_index FROM pokes WHERE id = $1",
                    selected_id,
                )
            else:
                await ctx.send(
                    "You do not have a selected pokemon and the item you are trying to buy requires one!\nUse `/select` to select a pokemon."
                )
                return
            # These items DO need the selected pokemon
            if item_name == "ability_capsule":
                ab_ids = []
                form_info = await ctx.bot.db[1].forms.find_one(
                    {"identifier": pokename.lower()}
                )
                async for record in ctx.bot.db[1].poke_abilities.find(
                    {"pokemon_id": form_info["pokemon_id"]}
                ):
                    ab_ids.append(record["ability_id"])
                if len(ab_ids) <= 1:
                    await ctx.send("That Pokemon cannot have its ability changed!")
                    return
                ab_index = (ab_index + 1) % len(ab_ids)
                new_ab = ab_ids[ab_index]
                await pconn.execute(
                    "UPDATE pokes SET ability_index = $1 WHERE id = $2", ab_index, _id
                )
                ability = (await ctx.bot.db[1].abilities.find_one({"id": new_ab}))[
                    "identifier"
                ]
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                    vat_price,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You have successfully changed your Pokémons ability to **{ability.capitalize( )}**"
                )
                return
            if item_name == "ev_reset":
                await pconn.execute(
                    "UPDATE pokes SET hpev = 0, atkev = 0, defev = 0, spatkev = 0, spdefev = 0, speedev = 0 WHERE id = $1",
                    _id,
                )
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $2 WHERE u_id = $1",
                    ctx.author.id,
                    vat_price,
                )
                await ctx.send(
                    "You have successfully reset the Effort Values (EVs) of your selected Pokemon!"
                )
                return
            if is_formed(pokename) and pokename != 'Gouging-fire':
                await ctx.send(
                    "You can not buy an item for a Form. Use `/deform` to de-form your Pokemon!"
                )
                return
            helditem = await pconn.fetchval(
                "SELECT hitem FROM pokes WHERE id = $1", _id
            )
            if not helditem.lower() == "none":
                await ctx.send("You already have an item equipped!")
                return
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                vat_price,
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE pokes SET hitem = $1 WHERE id = $2", item_name, _id
            )
            await ctx.send(
                f"You have successfully bought the {fancy_name.title()} for {price:,}!\nIt's been equipped to {pokename.title()}"
            )
            evolved = await evolve(
                ctx,
                ctx.bot,
                dict(await pconn.fetchrow("SELECT * FROM pokes WHERE id = $1", _id)),
                ctx.author,
                channel=ctx.channel,
            )

    @buy.command(name="daycare")
    async def buy_daycare(self, ctx, amount: int = 1):
        """Buy daycare spaces."""
        item = await ctx.bot.db[1].new_shop.find_one({"item": "daycare_space"})
        if not item:
            await ctx.send("That Item is not in the market")
            return

        price = item["price"]
        price *= abs(amount)
        async with ctx.bot.db[0].acquire() as pconn:
            bal = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
            )
            if bal is None:
                await ctx.send("You have not started!\nStart with `/start` first.")
                return
            if price > bal:
                await ctx.send(
                    f"You cannot afford that many daycare spaces! You need {price} credits, but you only have {bal}."
                )
                return
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins - $2, daycarelimit = daycarelimit + $3 WHERE u_id = $1",
                ctx.author.id,
                price,
                amount,
            )
        plural = "s" if amount != 1 else ""
        await ctx.send(f"You have successfully bought {amount} daycare space{plural}!")

    @buy.command(name="vitamins")
    async def buy_vitamins(
        self,
        ctx,
        item_name: Literal["Hp Up", "Protein", "Iron", "Calcium", "Zinc", "Carbos"],
        amount: int,
    ):
        amount = max(0, amount)
        item_name = item_name.replace(" ", "_").lower()
        item_info = await ctx.bot.db[1].new_shop.find_one({"item": item_name})
        if item_info is None:
            await ctx.send("That item is not in the market.")
            return

        async with ctx.bot.db[0].acquire() as pconn:
            total_price = amount * 100
            _id = await pconn.fetchval(
                "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
            )
            pokename = await pconn.fetchval(
                "SELECT pokname FROM pokes WHERE id = $1", _id
            )
            if pokename is None:
                await ctx.send(
                    "You don't have a pokemon selected!\nSelect one with `/select` first."
                )
                return
            async with pconn.transaction():
                try:
                    await pconn.execute(
                        "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                        ctx.bot.misc.get_vat_price(total_price),
                        ctx.author.id,
                    )
                except:
                    await ctx.send(f"You do not have {total_price} credits!")
                    return
                try:
                    if item_name == "zinc":
                        await pconn.execute(
                            "UPDATE pokes SET spdefev = spdefev + $1 WHERE id = $2",
                            amount,
                            _id,
                        )
                    elif item_name == "hp_up":
                        await pconn.execute(
                            "UPDATE pokes SET hpev = hpev + $1 WHERE id = $2",
                            amount,
                            _id,
                        )
                    elif item_name == "protein":
                        await pconn.execute(
                            "UPDATE pokes SET atkev = atkev + $1 WHERE id = $2",
                            amount,
                            _id,
                        )
                    elif item_name == "calcium":
                        await pconn.execute(
                            "UPDATE pokes SET spatkev = spatkev + $1 WHERE id = $2",
                            amount,
                            _id,
                        )
                    elif item_name == "iron":
                        await pconn.execute(
                            "UPDATE pokes SET defev = defev + $1 WHERE id = $2",
                            amount,
                            _id,
                        )
                    elif item_name == "carbos":
                        await pconn.execute(
                            "UPDATE pokes SET speedev = speedev + $1 WHERE id = $2",
                            amount,
                            _id,
                        )
                    await ctx.send(
                        f"You have successfully bought {amount} {item_name} for your {pokename}"
                    )
                except:
                    await ctx.send(
                        "Your Pokemon has maxed all 510 EVs or 252 EVs for that stat."
                    )

    @buy.command(name="energy")
    async def _energy_refill(self, ctx):
        """Buy energy refills using this command"""

        cooldown = (
            await ctx.bot.redis_manager.redis.execute(
                "HMGET", "energycooldown", str(ctx.author.id)
            )
        )[0]

        if cooldown is None:
            cooldown = 0
        else:
            cooldown = float(cooldown.decode("utf-8"))

        if cooldown > time.time():
            reset_in = round(cooldown - time.time())
            cooldown = str(timedelta(seconds=reset_in))
            await ctx.send(f"Command on cooldown for {cooldown}")
            return

        # Flipped these so that players who don't have the 25k trigger the redis cooldown
        async with ctx.bot.db[0].acquire() as pconn:
            msg = await ctx.send(embed=make_embed(title="Refilling all your Energy..."))
            try:
                if ctx.author.id in (455277032625012737, 449401742568849409):
                    await pconn.execute(
                        "UPDATE users SET mewcoins = mewcoins - 25000, npc_energy = 10 WHERE u_id = $1",
                        ctx.author.id,
                    )
                    await msg.edit(embed=make_embed(title="SMH!"))
                else:
                    await pconn.execute(
                        "UPDATE users SET mewcoins = mewcoins - 25000, energy = 10 WHERE u_id = $1",
                        ctx.author.id,
                    )
                    await msg.edit(
                        embed=make_embed(title="Your energy has been refilled!")
                    )
            except:
                await msg.edit(
                    embed=make_embed(
                        title=f"You don't have 25000{ctx.bot.misc.emotes['CREDITS']}"
                    )
                )
                return

        patreon = await ctx.bot.patreon_tier(ctx.author.id)
        if ctx.author.id in (455277032625012737, 449401742568849409):
            await ctx.bot.redis_manager.redis.execute(
                "HMSET",
                "energycooldown",
                str(ctx.author.id),
                str(time.time() + 60 * 1.25),
            )
        elif patreon in ("Crystal Tier", "Silver Tier"):
            await ctx.bot.redis_manager.redis.execute(
                "HMSET",
                "energycooldown",
                str(ctx.author.id),
                str(time.time() + 60 * 60 * 4),
            )
        else:
            await ctx.bot.redis_manager.redis.execute(
                "HMSET",
                "energycooldown",
                str(ctx.author.id),
                str(time.time() + 60 * 60 * 12),
            )

    @buy.command(name="candy")
    async def buy_candy(self, ctx, amount: int = 1):
        async with ctx.bot.db[0].acquire() as pconn:
            _id = await pconn.fetchval(
                "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
            )
            if _id is None:
                await ctx.send("You need to select a pokemon first!")
                return
            det = await pconn.fetchrow("SELECT * FROM pokes WHERE id = $1", _id)
            credits = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
            )
        name = det["pokname"]
        poke_id = det["id"]
        level = det["pokelevel"]
        happiness = det["happiness"]
        use_amount = max(0, amount)
        use_amount = min(100 - level, use_amount)
        buy_amount = use_amount
        if buy_amount == 0:
            buy_amount = 1
        price = buy_amount * 100
        if buy_amount == 1:
            string = "candy"
        else:
            string = "candies"
        if price > credits:
            await ctx.send(
                f"You do not have {price} credits for {buy_amount} Rare {string}"
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            # This try should not be necessary, but this keeps trying to assign lvl 101 pokes for no reason, and needs debugging
            try:
                await pconn.execute(
                    "UPDATE pokes SET pokelevel = pokelevel + $1 WHERE id = $2",
                    use_amount,
                    poke_id,
                )
            except Exception as e:
                ctx.bot.logger.warning(
                    f"Tried to give more levels than allowed - Poke: {poke_id} | Expected level - {level + use_amount}"
                )
                await ctx.send(
                    "Sorry, I can't do that right now. Try again in a moment."
                )
                return
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                ctx.bot.misc.get_vat_price(price),
                ctx.author.id,
            )
            pokemon_details = await pconn.fetchrow(
                "SELECT * FROM pokes WHERE id = $1", poke_id
            )
        level_total = level + use_amount
        await ctx.send(
            f"Your {name} has successfully leveled up to Level {level_total}."
        )
        await evolve(
            ctx,
            ctx.bot,
            dict(pokemon_details),
            ctx.author,
            channel=ctx.channel,
            override_lvl_100=True,
        )

    @buy.command(name="chest")
    @discord.app_commands.describe(
        chest_type="The type of chest you want to buy.",
        credits_or_redeems="Use credits or redeems to buy chest.",
    )
    async def buy_chest(
        self,
        ctx,
        chest_type: Literal["Rare", "Mythic", "Legend"],
        credits_or_redeems: Literal["Credits", "Redeems"],
    ):
        """Buy a gleam chest."""
        ct = chest_type.lower().strip()
        cor = credits_or_redeems.lower()
        if ct not in ("rare", "mythic", "legend"):
            await ctx.send(
                f'"`{ct}`" is not a valid chest type! Choose one of Rare, Mythic, or Legend.'
            )
            return
        if cor not in ("credits", "redeems"):
            await ctx.send('Specify either "credits" or "redeems"!')
            return
        price = {
            "credits": {"rare": 600000, "mythic": 1250000, "legend": 3000000},
            "redeems": {"rare": 12, "mythic": 25, "legend": 55},
        }[cor][ct]
        if not await ConfirmView(
            ctx, f"Are you sure you want to buy a {ct} chest for {price} {cor}?\n"
        ).wait():
            await ctx.send("Purchase cancelled.")
            return

        async with ctx.bot.db[0].acquire() as pconn:
            if cor == "credits":
                bal = await pconn.fetchval(
                    "SELECT mewcoins FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                if bal is None:
                    await ctx.send("You have not started!\nStart with `/start` first.")
                    return
                if bal < price:
                    await ctx.send(
                        f"You do not have the {price} credits you need to buy a {ct} chest!"
                    )
                    return

                await pconn.execute(
                    "INSERT INTO cheststore VALUES ($1, 0, 0, 0, 0) ON CONFLICT DO NOTHING",
                    ctx.author.id,
                )
                info = await pconn.fetchrow(
                    "SELECT * FROM cheststore WHERE u_id = $1", ctx.author.id
                )
                info = {
                    "u_id": info["u_id"],
                    "rare": info["rare"],
                    "mythic": info["mythic"],
                    "legend": info["legend"],
                    "restock": int(info["restock"]),
                }

                max_chests = 5
                restock_time = 604800
                if info["restock"] <= int(time.time() // restock_time):
                    await pconn.execute(
                        "UPDATE cheststore SET rare = 0, mythic = 0, legend = 0, restock = $1 WHERE u_id = $2",
                        str(int(time.time() // restock_time) + 1),
                        ctx.author.id,
                    )
                    info = {
                        "u_id": ctx.author.id,
                        "rare": 0,
                        "mythic": 0,
                        "legend": 0,
                        "restock": int(time.time() // restock_time) + 1,
                    }
                if info[ct] + 1 > max_chests:
                    await ctx.send(
                        f"You can't buy more than {max_chests} per week using credits!  You've already bought {info[ct]}."
                    )
                    return
                
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                    ctx.bot.misc.get_vat_price(price),
                    ctx.author.id,
                )
                if ct == "rare":
                    await pconn.execute(
                        "UPDATE cheststore SET rare = rare + 1 WHERE u_id = $1",
                        ctx.author.id,
                    )
                elif ct == "mythic":
                    await pconn.execute(
                        "UPDATE cheststore SET mythic = mythic + 1 WHERE u_id = $1",
                        ctx.author.id,
                    )
                elif ct == "legend":
                    await pconn.execute(
                        "UPDATE cheststore SET legend = legend + 1 WHERE u_id = $1",
                        ctx.author.id,
                    )
            elif cor == "redeems":
                bal = await pconn.fetchval(
                    "SELECT redeems FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                if bal is None:
                    await ctx.send("You have not started!\nStart with `/start` first.")
                    return
                if bal < price:
                    await ctx.send(
                        f"You do not have the {price} redeems you need to buy a {ct} chest!"
                    )
                    return
                await pconn.execute(
                    "UPDATE users SET redeems = redeems - $1 WHERE u_id = $2",
                    price,
                    ctx.author.id,
                )
            else:  # safe-guard, should never be hit
                return
            item = ct + "_chest"
            await ctx.bot.commondb.add_bag_item(ctx.author.id, item, 1, True)
        await ctx.send(
            f"You have successfully bought a {ct} chest for {price} {cor}!\n"
            f"You can open it with `/open {ct}`."
        )

    @buy.command(name="redeems")
    async def buy_redeems(self, ctx, amount: int = None):
        f"""Buy redeems using Credits"""
        if amount and amount < 1:
            await ctx.send("Nice try...")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            if not await pconn.fetchval(
                "SELECT exists(SELECT * from users WHERE u_id = $1)", ctx.author.id
            ):
                await ctx.send("You have not started!\nStart with `/start` first.")
                return

            await pconn.execute(
                "INSERT INTO redeemstore VALUES ($1, 0, 0) ON CONFLICT DO NOTHING",
                ctx.author.id,
            )
            info = await pconn.fetchrow(
                "SELECT * FROM redeemstore WHERE u_id = $1", ctx.author.id
            )

        if not info:
            info = {"u_id": ctx.author.id, "bought": 0, "restock": 0}
        else:
            info = {
                "u_id": info["u_id"],
                "bought": info["bought"],
                "restock": int(info["restock"]),
            }

        max_redeems = 5
        restock_time = 604800
        credits_per_redeem = 60000

        if info["restock"] <= int(time.time() // restock_time):
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE redeemstore SET bought = 0, restock = $1 WHERE u_id = $2",
                    str(int(time.time() // restock_time) + 1),
                    ctx.author.id,
                )
            info = {
                "u_id": ctx.author.id,
                "bought": 0,
                "restock": int(time.time() // restock_time) + 1,
            }

        if not amount:
            if info["restock"] != 0:
                desc = f"You have bought {info['bought']} redeems this week.\n"
                if info["bought"] >= max_redeems:
                    desc += "You cannot buy any more this week."
                else:
                    desc += "Buy more using `/buy redeems <amount>`!"
                embed = discord.Embed(
                    title="Buy redeems",
                    description=desc,
                    color=0xFFB6C1,
                )
                embed.set_footer(text="Redeems restock every Wednesday at 8pm ET.")
            else:
                embed = discord.Embed(
                    title="Buy redeems",
                    description="You haven't bought any redeems yet! Use `/buy redeems <amount>`!",
                    color=0xFFB6C1,
                )

            await ctx.send(embed=embed)
        else:
            if info["bought"] + amount > max_redeems:
                await ctx.send(
                    f"You can't buy more than {max_redeems} per week!  You've already bought {info['bought']}."
                )
                return

            async with ctx.bot.db[0].acquire() as pconn:
                bal = await pconn.fetchval(
                    "SELECT mewcoins FROM users WHERE u_id = $1",
                    ctx.author.id,
                )

            price = amount * credits_per_redeem

            if bal < price:
                await ctx.send(
                    f"You do not have the {price} credits to buy those redeems!"
                )
                return

            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1, mewcoins = mewcoins - $2 WHERE u_id = $3",
                    amount,
                    price,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE redeemstore SET bought = bought + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
                if info["restock"] == 0:
                    await pconn.execute(
                        "UPDATE redeemstore SET restock = $1 WHERE u_id = $2",
                        str(int(time.time() // restock_time) + 1),
                        ctx.author.id,
                    )

            await ctx.send(
                f"You have successfully bought {amount} redeems for {price} credits!"
            )


async def setup(bot):
    await bot.add_cog(Items(bot))
