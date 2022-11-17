import discord
import random
import asyncio

from discord.ext import commands
from typing import Literal
from mewcogs.pokemon_list import pList, LegendList, natlist, pseudoList, ubList, starterList
from mewutils.misc import ConfirmView, ListSelectView


class Chests(commands.Cog):
    """Open and view info on Radiant Chests."""

    def __init__(self, bot):
        self.bot = bot
        # currently available gleam pokemon, ("Pokemon")
        self.CURRENTLY_ACTIVE = (
            "Absol", "Palkia", "Hoppip", "Rockruff", "Kartana", "Zorua-hisui", "Growlithe", "Smeargle"
        ) 
        # currently available event radiants, {"Pokemon": "String when they get that poke!\n"}
        self.EVENT_ACTIVE = {}
        # packs that can be bought with ;radiant, (("Pack Desc", <int - Price in radiant gems>))
        self.PACKS = (
            ("Shiny Multiplier x1", 5),
            ("Battle Multiplier x1", 5),
            ("IV Multiplier x1", 5),
            ("Breeding Multiplier x1", 5),
            ("Legend Chest", 75),
            ("Gleam Pokemon (common & starter)", 150),
            ("Gleam Pokemon (legend & pseudo)", 300),
        )
        self.CREDITS_PER_MULTI = 100000
        legend = set(LegendList + ubList + pseudoList)
        common = set(pList) - legend
        self.LEGEND = set(self.CURRENTLY_ACTIVE) & legend
        self.COMMON = set(self.CURRENTLY_ACTIVE) & common

    # async def log_chest(self, ctx):
    #     async with ctx.bot.db[0].acquire() as pconn:
    #         await pconn.execute(
    #             "INSERT INTO skylog (u_id, command, args, jump, time) VALUES ($1, $2, $3, $4, $5)",
    #             ctx.author.id,
    #             ctx.command.qualified_name,
    #             " ".join([str(x) for x in ctx.args]),
    #             ctx.jump_url,
    #             ctx.created_at.replace(tzinfo=None),
    #         )

    async def _maybe_spawn_event(self, ctx, chance):
        """
        Temporary method for spawning additional event pokemon.
        Spawns an event radiant for users who do not have one.
        
        Returns a string for user facing output.
        """
        if random.random() > chance:
            return ""
        if not self.EVENT_ACTIVE:
            return ""
        options = []
        async with ctx.bot.db[0].acquire() as pconn:
            for p in self.EVENT_ACTIVE:
                if not await pconn.fetchval(
                    "SELECT count(id) FROM pokes WHERE id in (select unnest(u.pokes) from users u where u.u_id = $1) AND radiant = true AND pokname = $2",
                    ctx.author.id, p
                ):
                    options.append(p)
        if not options:
            return ""
        poke = random.choice(options)
        await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, poke, skin='gleam')
        return self.EVENT_ACTIVE[poke]

    @commands.hybrid_group()
    async def open(self, ctx):
        ...
    
    @open.group()
    async def chest(self, ctx):
        ...

    @chest.command()
    async def common(self, ctx):
        """Open a common chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "common chest" not in inventory or inventory["common chest"] <= 0:
                await ctx.send("You do not have any Common Chests!")
                return
            inventory["common chest"] = inventory.get("common chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )

        reward = random.choices(
            ("gleam", "chest", "ev", "poke", "redeem", "cred"),
            weights=(0.005, 0.015, 0.1, 0.2, 0.25, 0.43),
        )[0]

        if reward == "gleam":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='gleam')
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a gleam {pokemon}!**\n"
        elif reward == "chest":
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["rare chest"] = inventory.get("rare chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
            msg = "You received a Rare Chest!\n"
        elif reward == "redeem":
            amount = 1
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = "You received 1 redeem!\n"
        elif reward == "ev":
            amount = 250
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET evpoints = evpoints + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} ev points!\n"
        elif reward == "cred":
            amount = random.randint(10, 25) * 1000
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} credits!\n"
        elif reward == "poke":
            pokemon = random.choice(pList)
            pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon)
            msg = f"You received a {pokedata.emoji}{pokemon}!\n"
        gems = 1
        if gems:
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + gems
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
            msg += f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!\n"
        msg += await self._maybe_spawn_event(ctx, .15)
        await ctx.send(msg)

    
    @chest.command()
    async def rare(self, ctx):
        """Open a rare chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "rare chest" not in inventory or inventory["rare chest"] <= 0:
                await ctx.send("You do not have any Rare Chests!")
                return
            inventory["rare chest"] = inventory.get("rare chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        reward = random.choices(
            ("radiant", "redeem", "chest", "boostedshiny", "shiny"),
            weights=(0.02, 0.175, 0.20, 0.15, 0.455),
        )[0]
        if reward == "radiant":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='gleam')
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a gleam {pokemon}!**\n"
        elif reward == "redeem":
            amount = random.randint(4, 6)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} redeems!\n"
        elif reward == "chest":
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["mythic chest"] = inventory.get("mythic chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
            msg = "You received a Mythic Chest!\n"
        elif reward == "shiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True)
            msg = f"You received a shiny {pokemon}!\n"
        elif reward == "boostedshiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True, boosted=True)
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        gems = random.randint(1, 2)
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            inventory["radiant gem"] = inventory.get("radiant gem", 0) + gems
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        msg += f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!\n"
        msg += await self._maybe_spawn_event(ctx, .20)
        await ctx.send(msg)
    
    @chest.command()
    async def mythic(self, ctx):
        """Open a mythic chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "mythic chest" not in inventory or inventory["mythic chest"] <= 0:
                await ctx.send("You do not have any Mythic Chests!")
                return
            inventory["mythic chest"] = inventory.get("mythic chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        reward = random.choices(
            ("radiant", "boostedleg", "redeem", "chest", "shiny", "boostedshiny"),
            weights=(0.12, 0.04, 0.22, 0.20, 0.15, 0.27),
        )[0]

        if reward == "redeem":
            amount = random.randint(7, 15)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} redeems!\n"

        elif reward == "chest":
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["legend chest"] = inventory.get("legend chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
            msg = "You received a Legend Chest!\n"

        elif reward == "boostedleg":
            pokemon = random.choice(LegendList)
            pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True)
            msg = f"You received a boosted IV {pokedata.emoji}{pokemon}!\n"

        elif reward == "radiant":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='gleam')
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a gleam {pokemon}!**\n"

        elif reward == "shiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True)
            msg = f"You received a shiny {pokemon}!\n"

        elif reward == "boostedshiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True, boosted=True)
            msg = f"You received a shiny boosted IV {pokemon}!\n"

        gems = random.randint(8, 11)
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            inventory["radiant gem"] = inventory.get("radiant gem", 0) + gems
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        msg += f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!\n"
        msg += await self._maybe_spawn_event(ctx, .25)
        await ctx.send(msg)

    @chest.command()
    async def legend(self, ctx):
        """Open a legend chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "legend chest" not in inventory or inventory["legend chest"] <= 0:
                await ctx.send("You do not have any Legend Chests!")
                return
            inventory["legend chest"] = inventory.get("legend chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id
            )

        # Going to save this here for when we replace vouchers
        #voucher_chance = 0 if ctx.author.id in (399855039130238986,) else 0.001
        #reward = random.choices(
            #("custom", "boostedshinylegendary", "redeem", "radiant", "boostedshiny"),
            #weights=(voucher_chance, 0.014, 0.31, 0.235, 0.44),
        #)[0]

        # This will replace it until we revisit the voucher
        reward = random.choices(
            ("boostedshinylegendary", "redeem", "radiant", "boostedshiny"),
            weights=(0.015, 0.31, 0.235, 0.44),
        )[0]

        if reward == "custom":
            msg = "You have received a public voucher that allows you to submit your own recolor with background for any unreleased gleam pokemon, and it will be added to the following months lineup for everyone to obtain! Message Sky in the official server for more information!\nAlso, you of course get the one you design guaranteed. "
            await ctx.bot.get_partial_messageable(998291646443704320).send(f"<@631840748924436490> USER ID `{ctx.author.id}` HAS WON A 'Totally Custom Pokemon skin PUBLIC voucher'!")
        elif reward == "boostedshinylegendary":
            pokemon = random.choice(LegendList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True, shiny=True)
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        elif reward == "boostedshiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True, shiny=True)
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        elif reward == "redeem":
            amount = random.randint(30, 50)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} redeems!\n"
        elif reward == "radiant":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='gleam', boosted=True)
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a boosted gleam {pokemon}!**\n"
        gems = random.randint(10, 15)
        async with ctx.bot.db[0].acquire() as pconn:
            inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            inv["radiant gem"] = inv.get("radiant gem", 0) + gems
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inv,
                ctx.author.id,
            )
        msg += f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!\n"
        msg += await self._maybe_spawn_event(ctx, .33)
        await ctx.send(msg)


    @chest.command(name="art")
    async def art_team(self, ctx):
        """Open an art chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "art chest" not in inventory or inventory["art chest"] <= 0:
                await ctx.send("You do not have any Art Chests!")
                return
            inventory["art chest"] = inventory.get("art chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id
            )

        reward = random.choices(
            ("boostedshinylegendary", "redeem", "radiant", "gleam", "boostedgleam", "boostedshiny"),
            weights=(0.015, 0.05, 0.15, 0.315, 0.235, 0.235),
        )[0]

        if reward == "custom":
            msg = "You have received a public voucher that allows you to submit your own recolor with background for any unreleased gleam pokemon, and it will be added to the following months lineup for everyone to obtain! Message Sky in the official server for more information!\nAlso, you of course get the one you design guaranteed. "
            await ctx.bot.get_partial_messageable(998291646443704320).send(f"<@631840748924436490> USER ID `{ctx.author.id}` HAS WON A 'Totally Custom Pokemon skin PUBLIC voucher'!")
        elif reward == "boostedshinylegendary":
            pokemon = random.choice(LegendList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True, shiny=True)
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        elif reward == "boostedshiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True, shiny=True)
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        elif reward == "redeem":
            amount = random.randint(30, 50)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} redeems!\n"

        elif reward == "radiant":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='radiant')
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a boosted radiant {pokemon}!**\n"

        elif reward == "gleam":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='gleam')
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a boosted gleam {pokemon}!**\n"


        elif reward == "boostedgleam":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='gleam', boosted=True)
            msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a boosted gleam {pokemon}!**\n"


        gems = random.randint(10, 15)
        async with ctx.bot.db[0].acquire() as pconn:
            inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            inv["radiant gem"] = inv.get("radiant gem", 0) + gems
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inv,
                ctx.author.id,
            )
        msg += f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!\n"
        msg += await self._maybe_spawn_event(ctx, .33)
        await ctx.send(msg)


    @commands.hybrid_group()
    async def gleam(self, ctx):
        ...
    
    @gleam.command()
    async def packs(self, ctx):
        """Get Information of Gleam Packs"""
        desc = ""
        for idx, pack in enumerate(self.PACKS, start=1):
            desc += f"**{idx}.** __{pack[0]}__ - <a:radiantgem:774866137472827432>x{pack[1]}\n"
        desc += f"\nUse `/gleam` with the number you want to buy."
        e = discord.Embed(
            title="Gleam Gem Shop",
            description=desc,
            color=ctx.bot.get_random_color(),
        )
        await ctx.send(embed=e)
        
    @gleam.command()
    async def pack(self, ctx, pack: Literal["1. Shiny Multiplier x1", "2. Battle Multiplier x1", "3. IV Multiplier x1", "4. Breeding Multiplier x1", "5. Legend Chest", "6. Gleam Pokemon (common & starter)", "7. Gleam Pokemon (legend & pseudo)"]):
        """Spend your gleam gems to obtain gleam Pokemon."""
        packnum = int(pack[0])
        if packnum < 1 or packnum > len(self.PACKS):
            await ctx.send("That is not a valid pack number.")
            return
        pack = self.PACKS[packnum - 1]
        
        if not await ConfirmView(ctx, f"Are you sure you want to buy {pack[0]} for <a:radiantgem:774866137472827432>x{pack[1]}?").wait():
            await ctx.send("Purchase cancelled.")
            return

        choice = ""
        if packnum in (6, 7):
            if packnum == 6:
                options = list(self.COMMON)
            elif packnum == 7:
                options = list(self.LEGEND)
            if not options:
                await ctx.send(
                    "There are currently no valid pokemon in the pool. Please try again later."
                )
                return
            choice = await ListSelectView(ctx, "Which pokemon do you want?", options).wait()
            if choice is None:
                await ctx.send("You did not select in time, cancelling.")
                return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if inventory.get("radiant gem", 0) < pack[1]:
                await ctx.send("You cannot afford that pack!")
                return
            inventory["radiant gem"] = inventory.get("radiant gem", 0) - pack[1]
            if packnum in (1, 2, 3, 4):
                if packnum == 1:
                    item = "shiny-multiplier"
                elif packnum == 2:
                    item = "battle-multiplier"
                elif packnum == 3:
                    item = "iv-multiplier"
                elif packnum == 4:
                    item = "breeding-multiplier"
                if inventory.get(item, 0) >= 50:
                    await ctx.send("You have hit the cap for that multiplier!")
                    return
                inventory[item] = min(inventory.get(item, 0) + 1, 50)
            elif packnum == 5:
                inventory["legend chest"] = inventory.get("legend chest", 0) + 1
            elif packnum in (6, 7):
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, choice, skin='gleam', boosted=True)
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        await ctx.send(
            f"You have successfully bought {pack[0]} for <a:radiantgem:774866137472827432>x{pack[1]}."
        )


async def setup(bot):
    await bot.add_cog(Chests(bot))
