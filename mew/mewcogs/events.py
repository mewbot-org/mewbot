import os
from unicodedata import name
import discord
from discord.ext import commands
from mewcogs.pokemon_list import *

from mewutils.checks import tradelock, check_mod
from mewutils.misc import get_file_name, ConfirmView
import random
import asyncio
import time
from collections import defaultdict
from datetime import datetime


ORANGE = 0xF4831B
RED_GREEN = [0xBB2528, 0x146B3A]


class Events(commands.Cog):
    """Various seasonal events in Mewbot."""

    def __init__(self, bot):
        self.bot = bot
        # Seasonal toggles
        self.EASTER_DROPS = False
        self.EASTER_COMMANDS = False
        self.HALLOWEEN_DROPS = True
        self.HALLOWEEN_COMMANDS = True
        self.CHRISTMAS_DROPS = False
        self.CHRISTMAS_COMMANDS = False
        self.EGGS = (
            ("bidoof", "caterpie", "pidgey", "magikarp",
             "spinarak", "tentacruel", "togepi", "bellsprout"),
            ("ralts", "porygon", "farfetchd", "cubone", "omastar", "chansey"),
            ("gible", "bagon", "larvitar", "dratini"),
            ("kyogre", "dialga"),
        )
        self.EGG_EMOJIS = {
            "bidoof": "<:common1:824435458200436787>",
            "caterpie": "<:common2:824435458498101249>",
            "pidgey": "<:common3:824435458515009596>",
            "magikarp": "<:common4:824435458552758282>",
            "spinarak": "<:common5:824435458351956019>",
            "tentacruel": "<:common6:824435458552365056>",
            "togepi": "<:common7:824435458724724816>",
            "bellsprout": "<:common8:824435458633236501>",
            "chansey": "<:uncommon6:824435458929852426>",
            "omastar": "<:uncommon5:824435458779906068>",
            "cubone": "<:uncommon4:824435458737831996>",
            "farfetchd": "<:uncommon3:824435458758934538>",
            "porygon": "<:uncommon2:824435458824994846>",
            "ralts": "<:uncommon1:824435458317877249>",
            "dratini": "<:rare4:824435458753691648>",
            "larvitar": "<:rare3:824435458359820359>",
            "bagon": "<:rare2:824435458716991499>",
            "gible": "<:rare1:824435458439381083>",
            "kyogre": "<:legend1:824435458599682090>",
            "dialga": "<:legend2:824435458451832873>",
        }
        self.HALLOWEEN_RADIANT = [
            'Absol',
            'Litwick',
            'Gligar',
            'Misdreavus',
            'Yamper',
            'Togepi',
            'Marshadow',
            'Shroomish',
            'Hatenna'
        ]
        # "Poke name": ["Super effective (2)", "Not very (1)", "No effect (0)", "No effect (0)"]
        self.CHRISTMAS_MOVES = {
            'Surskit': ['Thunderbolt', 'Razor Leaf', 'Bubble', 'Aqua Ring'],
            'Absol': ['Draining Kiss', 'Aqua Tail', 'Shadow Sneak', 'Telekinesis'],
            'Litwick': ['Scald Super', 'Dragon Claw', 'Fairy Wind', 'Will-o-wisp'],
            'Gligar': ['Hydro Pump', 'Earthquake ', 'Razor Leaf', ' Bug Buzz'],
            'Misdreavus': ['Payback', 'Psywave', 'Silver Wind', 'Vacuum Wave'],
            'Yamper': ['Mud Slap', 'Power Whip', 'Thunder Shock', 'Thunder Wave'],
            'Togepi': ['Acid Super', 'Water Shuriken', 'Bug Buzz', 'Dragon Rage'],
            'Marshadow': ['Bitter Malice', 'Fire Spin', 'Bug Bite', 'Low Kick'],
            'Shroomish': ['Dual Wingbeat', 'Grassy Glide', 'Hyper Voice', 'Leech Seed'],
            'Hatenna': ['Bite', 'Psyshock', 'Moonblast', 'Leer'],

        }

        self.UNOWN_WORD = None
        self.UNOWN_GUESSES = []
        self.UNOWN_MESSAGE = None
        self.UNOWN_CHARACTERS = [
            {
                'a': '<:emoji_1:980642261375275088>',
                'b': '<:emoji_2:980642329838887002>',
                'c': '<:emoji_3:980643284810604624>',
                'd': '<:emoji_4:980643355136524298>',
                'e': '<:emoji_5:980643389005525042>',
                'f': '<:emoji_6:980643421519749150>',
                'g': '<:emoji_7:980643480005128272>',
                'h': '<:emoji_8:980643523105792050>',
                'i': '<:emoji_9:980643960840142868>',
                'j': '<:emoji_10:980644034978648115>',
                'k': '<:emoji_11:980644080591720471>',
                'l': '<:emoji_12:980644136543735868>',
                'm': '<:emoji_13:980644168244289567>',
                'n': '<:emoji_14:980644255427084328>',
                'o': '<:emoji_15:980644320052916236>',
                'p': '<:emoji_16:980644377506492456>',
                'q': '<:emoji_17:980644413057421332>',
                'r': '<:emoji_18:980644457777086494>',
                's': '<:emoji_19:980644499971768380>',
                't': '<:emoji_20:980644531903025212>',
                'u': '<:emoji_21:980644565751054436>',
                'v': '<:emoji_22:980644667928477746>',
                'w': '<:emoji_23:980644751097348146>',
                'x': '<:emoji_24:980644781313097808>',
                'y': '<:emoji_25:980644826947129425>',
                'z': '<:emoji_26:980644947587923989>',
                '!': '<:emoji_27:980645036456828948>',
                '?': '<:emoji_28:980645086067032155>',
            },
            {
                'l': '<:emoji_29:980547575717429308>',
                'd': '<:emoji_30:980547603605381190>',
                'i': '<:emoji_31:980547628607623168>',
                'k': '<:emoji_32:980547656965324861>',
                'e': '<:emoji_33:980547682298900510>',
                'b': '<:emoji_34:980547714922188841>',
                'n': '<:emoji_35:980547739429507073>',
                'j': '<:emoji_36:980547764637282355>',
                'a': '<:emoji_37:980547791006875708>',
                'f': '<:emoji_38:980547820127920138>',
                'm': '<:emoji_39:980547852545691668>',
                'g': '<:emoji_40:980547877581496452>',
                'h': '<:emoji_41:980547904525725776>',
                'c': '<:emoji_42:980547940441534595>',
                'z': '<:emoji_43:980547990219546654>',
                'y': '<:emoji_44:980548022981230632>',
                '?': '<:emoji_45:980548050823032862>',
                '!': '<:emoji_46:980548077427499080>',
                'w': '<:emoji_47:980548114572267570>',
                'q': '<:emoji_48:980548145085821009>',
                'p': '<:emoji_49:980548175360303114>',
                'u': '<:emoji_50:980548210319818792>',
                'x': '<:emoji_43:980548384156946553>',
                't': '<:emoji_44:980548409784152136>',
                'o': '<:emoji_45:980548441509859409>',
                's': '<:emoji_46:980548467694895155>',
                'r': '<:emoji_47:980548498132979773>',
                'v': '<:emoji_48:980548529963556946>',
            },
        ]
        self.UNOWN_POINTS = {
            'a': 1,
            'b': 3,
            'c': 3,
            'd': 2,
            'e': 1,
            'f': 4,
            'g': 2,
            'h': 4,
            'i': 1,
            'j': 8,
            'k': 5,
            'l': 1,
            'm': 3,
            'n': 1,
            'o': 1,
            'p': 3,
            'q': 10,
            'r': 1,
            's': 1,
            't': 1,
            'u': 1,
            'v': 4,
            'w': 4,
            'x': 8,
            'y': 4,
            'z': 10,
            '!': 1,
            '?': 1,
        }
        self.UNOWN_WORDLIST = []
        try:
            with open(self.bot.app_directory / "shared" / "data" / "wordlist.txt") as f:
                self.UNOWN_WORDLIST = f.readlines().copy()
        except Exception:
            pass

    @commands.hybrid_group()
    async def easter(self, ctx: commands.Context):
        ...

    @easter.command(name="list")
    async def easter_list(self, ctx):
        """View your easter eggs."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the easter season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT * FROM eggs WHERE u_id = $1", ctx.author.id)
        if data is None:
            await ctx.send("You haven't found any eggs yet... Go find some!")
            return
        embed = discord.Embed(
            title=f"{ctx.author.name}'s eggs", color=0x6CB6E3)
        for idx, rarity in enumerate(("Common", "Uncommon", "Rare", "Legendary")):
            hold = ""
            owned = 0
            for egg in self.EGGS[idx]:
                if data[egg]:
                    hold += f"{self.EGG_EMOJIS[egg]} {egg.capitalize()} egg - {data[egg]}\n"
                    owned += 1
            if hold:
                embed.add_field(
                    name=f"{rarity} ({owned}/{len(self.EGGS[idx])})", value=hold)
        if not embed.fields:
            await ctx.send("You don't have any eggs right now... Go find some more!")
            return
        embed.set_footer(
            text=f"Use /easter buy to spend your eggs on a reward.")
        await ctx.send(embed=embed)

    @easter.command(name="buy")
    async def easter_buy(self, ctx, choice: int = None):
        """Convert your eggs into various rewards."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the easter season!")
            return
        if choice is None:
            msg = (
                "**Egg rewards:**\n"
                "**1.** One of each common egg -> 10k credits + 1 common chest\n"
                "**2.** One of each uncommon egg -> 25k credits + 2 common chests\n"
                "**3.** One of each rare egg -> 50k credits + 1 rare chest\n"
                "**4.** One of each legendary egg -> 50k credits + 1 mythic chest\n"
                "**5.** One of each egg -> Easter Shuckle (one time per user) or 1 legend chest\n"
                f"Use `/easter buy <num>` to buy one of these rewards."
            )
            await ctx.send(msg)
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT * FROM eggs WHERE u_id = $1", ctx.author.id)
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
        if inventory is None:
            await ctx.send(f"You haven't started!\nStart with `/start` first!")
            return
        if data is None:
            await ctx.send("You haven't found any eggs yet... Go find some!")
            return
        if choice == 1:
            if not all((data["bidoof"], data["caterpie"], data["pidgey"], data["magikarp"], data["spinarak"], data["tentacruel"], data["togepi"], data["bellsprout"])):
                await ctx.send("You do not have every common egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET bidoof = bidoof - 1, caterpie = caterpie - 1, pidgey = pidgey - 1, magikarp = magikarp - 1, "
                    "spinarak = spinarak - 1, tentacruel = tentacruel - 1, togepi = togepi - 1, bellsprout = bellsprout - 1 "
                    "WHERE u_id = $1", ctx.author.id
                )
                inventory["common chest"] = inventory.get(
                    "common chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 10000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 10k credits and 1 common chest.")
        elif choice == 2:
            if not all((data["ralts"], data["porygon"], data["farfetchd"], data["cubone"], data["omastar"], data["chansey"])):
                await ctx.send("You do not have every uncommon egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET ralts = ralts - 1, porygon = porygon - 1, farfetchd = farfetchd - 1, cubone = cubone - 1, "
                    "omastar = omastar - 1, chansey = chansey - 1 WHERE u_id = $1",
                    ctx.author.id
                )
                inventory["common chest"] = inventory.get(
                    "common chest", 0) + 2
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 25000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 25k credits and 2 common chests.")
        elif choice == 3:
            if not all((data["gible"], data["bagon"], data["larvitar"], data["dratini"])):
                await ctx.send("You do not have every rare egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET gible = gible - 1, bagon = bagon - 1, larvitar = larvitar - 1, dratini = dratini - 1 "
                    "WHERE u_id = $1",
                    ctx.author.id
                )
                inventory["rare chest"] = inventory.get("rare chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 50000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 50k credits and 1 rare chest.")
        elif choice == 4:
            if not all((data["kyogre"], data["dialga"])):
                await ctx.send("You do not have every legendary egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET kyogre = kyogre - 1, dialga = dialga - 1 WHERE u_id = $1",
                    ctx.author.id
                )
                inventory["mythic chest"] = inventory.get(
                    "mythic chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 50000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 50k credits and 1 mythic chest.")
        elif choice == 5:
            if not all(data[x] for x in self.EGG_EMOJIS.keys()):
                await ctx.send("You do not have every egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET bidoof = bidoof - 1, caterpie = caterpie - 1, pidgey = pidgey - 1, magikarp = magikarp - 1, "
                    "spinarak = spinarak - 1, tentacruel = tentacruel - 1, togepi = togepi - 1, bellsprout = bellsprout - 1, "
                    "ralts = ralts - 1, porygon = porygon - 1, farfetchd = farfetchd - 1, cubone = cubone - 1, omastar = omastar - 1, "
                    "chansey = chansey - 1, gible = gible - 1, bagon = bagon - 1, larvitar = larvitar - 1, dratini = dratini - 1, "
                    "kyogre = kyogre - 1, dialga = dialga - 1, got_radiant = true WHERE u_id = $1",
                    ctx.author.id
                )
                if data["got_radiant"]:
                    inventory["legend chest"] = inventory.get(
                        "legend chest", 0) + 1
                    await pconn.execute(
                        "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                        inventory, ctx.author.id
                    )
                    await ctx.send("You have received 1 legend chest.")
                else:
                    await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Shuckle", skin="easter")
                    await ctx.send("You have received an Easter Shuckle! Happy Easter!")
        else:
            await ctx.send(f"That is not a valid option. Use `/easter buy` to see all options.")

    @easter.command(name="convert")
    async def easter_convert(self, ctx, eggname: str = None):
        """Convert one of each egg from a lower tier to get an egg for a higher tier."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the easter season!")
            return
        if eggname is None:
            msg = (
                "**Convert one of each egg from a lower tier to a specific egg from a higher tier:**\n"
                "One of each common egg -> 1 uncommon egg\n"
                "One of each uncommon egg -> 1 rare egg\n"
                "One of each rare egg -> 1 legendary egg\n"
                f"Use `/easter convert <eggname>` to convert your eggs."
            )
            await ctx.send(msg)
            return
        eggname = eggname.lower()
        if eggname in self.EGGS[0]:
            await ctx.send("You cannot convert to a common egg!")
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT * FROM eggs WHERE u_id = $1", ctx.author.id)
        if data is None:
            await ctx.send("You haven't found any eggs yet... Go find some!")
            return
        # common -> uncommon
        if eggname in self.EGGS[1]:
            if not all((data["bidoof"], data["caterpie"], data["pidgey"], data["magikarp"], data["spinarak"], data["tentacruel"], data["togepi"], data["bellsprout"])):
                await ctx.send("You do not have every common egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET bidoof = bidoof - 1, caterpie = caterpie - 1, pidgey = pidgey - 1, magikarp = magikarp - 1, "
                    f"spinarak = spinarak - 1, tentacruel = tentacruel - 1, togepi = togepi - 1, bellsprout = bellsprout - 1, {eggname} = {eggname} + 1"
                    "WHERE u_id = $1", ctx.author.id
                )
            await ctx.send(f"Successfully converted one of every common egg into a {eggname} egg!")
        # uncommon -> rare
        elif eggname in self.EGGS[2]:
            if not all((data["ralts"], data["porygon"], data["farfetchd"], data["cubone"], data["omastar"], data["chansey"])):
                await ctx.send("You do not have every uncommon egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET ralts = ralts - 1, porygon = porygon - 1, farfetchd = farfetchd - 1, cubone = cubone - 1, "
                    f"omastar = omastar - 1, chansey = chansey - 1, {eggname} = {eggname} + 1 WHERE u_id = $1",
                    ctx.author.id
                )
            await ctx.send(f"Successfully converted one of every uncommon egg into a {eggname} egg!")
        # rare -> legendary
        elif eggname in self.EGGS[3]:
            if not all((data["gible"], data["bagon"], data["larvitar"], data["dratini"])):
                await ctx.send("You do not have every rare egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    f"UPDATE eggs SET gible = gible - 1, bagon = bagon - 1, larvitar = larvitar - 1, dratini = dratini - 1, {eggname} = {eggname} + 1 "
                    "WHERE u_id = $1",
                    ctx.author.id
                )
            await ctx.send(f"Successfully converted one of every rare egg into a {eggname} egg!")
        else:
            await ctx.send("That is not a valid egg name!")
            return

    @commands.hybrid_group()
    async def halloween(self, ctx):
        """Halloween commands."""
        pass

    @halloween.command(name="buy")
    async def halloween_buy(self, ctx, option: int):
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        # if option == 8:
            # await ctx.send("The holiday raffle has ended!")
            # return
        if option < 1 or option > 6:
            await ctx.send("That isn't a valid option. Select a valid option from `/halloween shop`.")
            return
        async with self.bot.db[0].acquire() as pconn:
            bal = await pconn.fetchrow("SELECT candy, bone, pumpkin FROM halloween WHERE u_id = $1", ctx.author.id)
            if bal is None:
                await ctx.send("You haven't gotten any halloween treats to spend yet!")
                return
            # Convert 50 candy for 1 potion
            if option == 1:
                if bal["candy"] < 50:
                    await ctx.send("You don't have enough Candy for that!")
                    return
                await pconn.execute("UPDATE halloween SET candy = candy - 50, bone = bone + 1 WHERE u_id = $1", ctx.author.id)
                await ctx.send("Successfully bought 1 <:mewbot_potion:1036332369076043776> for 50 <:mewbot_candy:1036332371038982264>.")
                return
            # Leave this here incase we add Missingno and Gleam purchase option
            """if option in (7, 8, 9):
                if bal["pumpkin"] < 1:
                    await ctx.send("You don't have enough Scary Masks for that!")
                    return
                await pconn.execute("UPDATE halloween SET pumpkin = pumpkin - 1 WHERE u_id = $1", ctx.author.id)
                if option == 7:
                    await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Missingno")
                    await ctx.send("Successfully bought a Missingno for 1 pumpkin.")
                elif option == 8:
                    await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, self.HALLOWEEN_RADIANT, skin='gleam')
                    await ctx.send(f"Successfully bought a {self.HALLOWEEN_RADIANT} for 1 pumpkin!")
                elif option == 9:
                    await pconn.execute("UPDATE halloween SET raffle = raffle + 1 WHERE u_id = $1", ctx.author.id)
                    await ctx.send("Successfully bought a raffle ticket for 1 <:mewbot_mask:1036332369818431580>!")
                return"""
            # Replaces the above while we don't offer those options
            # Raffle entry
            if option == 3:
                if bal["pumpkin"] < 1:
                    await ctx.send("You don't have enough Scary Masks for that!")
                    return
                await pconn.execute("UPDATE halloween SET pumpkin = pumpkin - 1 WHERE u_id = $1", ctx.author.id)
                await pconn.execute("UPDATE halloween SET raffle = raffle + 1 WHERE u_id = $1", ctx.author.id)
                await ctx.send("Successfully bought a raffle ticket for 1 <:mewbot_mask:1036332369818431580>!")
                return
            # Everything from this point below uses Potions as currency
            # Checks balance per price as below.
            price = [100, 8, 5, 25, 80][option - 2]
            if bal["bone"] < price:
                await ctx.send("You don't have enough <:mewbot_potion:1036332369076043776> for that!")
                return
            await pconn.execute("UPDATE halloween SET bone = bone - $2 WHERE u_id = $1", ctx.author.id, price)
            # Convert potions for mask
            if option == 2:
                await pconn.execute("UPDATE halloween SET pumpkin = pumpkin + 1 WHERE u_id = $1", ctx.author.id)
                await ctx.send(f"Successfully bought 1 Scary  for {price} <:mewbot_potion:1036332369076043776>.")
            # Spooky Chest
            if option == 4:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["spooky chest"] = inventory.get(
                    "spooky chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                await ctx.send(f"Successfully bought a Spooky Chest for {price} <:mewbot_potion:1036332369076043776>.")
            # Fleshy Chest
            elif option == 5:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["fleshy chest"] = inventory.get(
                    "fleshy chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                await ctx.send(f"Successfully bought a Fleshy Chest for {price} <:mewbot_potion:1036332369076043776>.")
            # Horrific Chest
            elif option == 6:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["horrific chest"] = inventory.get(
                    "horrific chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                await ctx.send(f"Successfully bought a Horrific Chest for {price} <:mewbot_potion:1036332369076043776>.")

    @halloween.command(name="inventory")
    async def halloween_inventory(self, ctx):
        """Check your halloween inventory."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT candy, bone, pumpkin FROM halloween WHERE u_id = $1", ctx.author.id)
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
        if data is None:
            await ctx.send("You haven't gotten any halloween treats yet!")
            return
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Halloween Inventory",
            description="Use `/halloween shop` to see what you can spend your treats on!",
            color=ORANGE,
        )
        if data["candy"]:
            embed.add_field(
                name="Mewbot Candy", value=f"{data['candy']}x <:mewbot_candy:1036332371038982264>")
        if data["bone"]:
            embed.add_field(
                name="Sus Potion", value=f"{data['bone']}x <:mewbot_potion:1036332369076043776>")
        if data["pumpkin"]:
            embed.add_field(
                name="Scary Masks", value=f"{data['pumpkin']}x <:mewbot_mask:1036332369818431580>")
        if inventory.get("spooky chest", 0):
            embed.add_field(name="Spooky Chests",
                            value=f"{inventory.get('spooky chest', 0)}x")
        if inventory.get("fleshy chest", 0):
            embed.add_field(name="Fleshy Chests",
                            value=f"{inventory.get('fleshy chest', 0)}x")
        if inventory.get("horrific chest", 0):
            embed.add_field(name="Horrific Chests",
                            value=f"{inventory.get('horrific chest', 0)}x")

        embed.set_footer(
            text="Make sure to join our Official Server for all event updates!")
        await ctx.send(embed=embed)

    @halloween.command(name="shop")
    async def halloween_shop(self, ctx):
        """Check the halloween shop."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        # desc = (
            # "**Option# | Price | Item**\n"
            #"**1** | 50 candy | 1 Sus Potion\n"
            #"**2** | 5 Potions | Spooky Chest\n"
            #"**3** | 25 Potions | Fleshy Chest\n"
            #"**4** | 80 Potions | Horrific Chest\n"
            #"**5** | 150 Potions | 1 pumpkin\n"
            #"**6** | 1 Mask | Missingno\n"
            #"**7** | 1 Mask | Halloween radiant\n"
            #"**8** | 1 Mask | 1 Halloween raffle entry\n"
        # )
        embed = discord.Embed(
            title="Halloween Shop",
            color=ORANGE,
            description="Use /halloween buy with an option number to buy that item!",
        )
        embed.add_field(
            name="1. 1 Sus Potion",
            value="50 <:mewbot_candy:1036332371038982264>",
            inline=True
        )
        embed.add_field(
            name="2. 1 Scary Mask",
            value="150 <:mewbot_potion:1036332369076043776>",
            inline=True
        )
        embed.add_field(
            name="3. 1 Raffle Entry",
            value="1 <:mewbot_mask:1036332369818431580>",
            inline=True
        )
        embed.add_field(
            name="4. Spooky Chest",
            value="5 <:mewbot_potion:1036332369076043776>",
            inline=True
        )
        embed.add_field(
            name="5. Fleshy Chest",
            value="25 <:mewbot_potion:1036332369076043776>",
            inline=True
        )
        embed.add_field(
            name="6. Horrific Chest",
            value="80 <:mewbot_potion:1036332369076043776>",
            inline=True
        )
        # embed.add_field(
        #name="7. Missingno",
        #value="1 <:mewbot_mask:1036332369818431580>",
        # inline=True
        # )
        # embed.add_field(
        #name="8. Halloween Radiant",
        #value="1 <:mewbot_mask:1036332369818431580>",
        # inline=True
        # )
        embed.set_footer(text="Use /halloween inventory to check your stash!")
        await ctx.send(embed=embed)

    @halloween.command(name="open_spooky")
    async def open_spooky(self, ctx):
        """Open a spooky chest."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "spooky chest" not in inventory or inventory["spooky chest"] <= 0:
                await ctx.send("You do not have any Spooky Chests!")
                return
            inventory["spooky chest"] = inventory.get("spooky chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
            reward = random.choices(
                ("gleam", "missingno", "redeem", "cred", "trick"),
                weights=(0.01, 0.19, 0.2, 0.3, 0.3),
            )[0]
            if reward == "gleam":
                pokemon = random.choice(self.HALLOWEEN_RADIANT)
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='halloween')
                msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a Halloween {pokemon}!**\n"
            elif reward == "redeem":
                amount = random.randint(1, 10)
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                        amount,
                        ctx.author.id,
                    )
                msg = "You received 1 redeem!\n"
            elif reward == "cred":
                amount = random.randint(25, 50) * 1000
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                        amount,
                        ctx.author.id,
                    )
                msg = f"You received {amount} credits!\n"
            elif reward == "missingno":
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Missingno")
                msg = f"You received a Missingno!\n"
            elif reward == "trick":
                await ctx.send("*Trick or treat?*\nI choose trick!\n*A ghost flies out of the empty box*")
                return
        bones = random.randint(1, 3)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE halloween SET bone = bone + $1 WHERE u_id = $2", bones, ctx.author.id)
        msg += f"You also received {bones} <:mewbot_potion:1036332369076043776>!\n"
        await ctx.send(msg)

    @halloween.command(name="open_fleshy")
    async def open_fleshy(self, ctx):
        """Open a fleshy chest."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "fleshy chest" not in inventory or inventory["fleshy chest"] <= 0:
                await ctx.send("You do not have any Fleshy Chests!")
                return
            inventory["fleshy chest"] = inventory.get("fleshy chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
            reward = random.choices(
                ("gleam", "rarechest", "mythicchest", "missingno", "trick"),
                weights=(0.15, 0.3, 0.10, 0.15, 0.3),
            )[0]

            if reward == "gleam":
                pokemon = random.choice(self.HALLOWEEN_RADIANT)
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='halloween')
                msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a Halloween {pokemon}!**\n"

            elif reward == "mythicchest":

                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["mythic chest"] = inventory.get(
                    "mythic chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                msg = "You received a Mythic Chest!\n"

            elif reward == "rarechest":
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

            elif reward == "missingno":
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Missingno")
                msg = f"You received a Missingno!\n"

            elif reward == "trick":
                await ctx.send("*Trick or treat?*\nI choose trick!\n*A ghost flies out of the empty box*")
                return

        bones = random.randint(3, 5)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE halloween SET bone = bone + $1 WHERE u_id = $2", bones, ctx.author.id)
        msg += f"You also received {bones} <:mewbot_potion:1036332369076043776>!\n"
        await ctx.send(msg)

    @halloween.command(name="open_horrific")
    async def open_horrific(self, ctx):
        """Open a horrific chest."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "horrific chest" not in inventory or inventory["horrific chest"] <= 0:
                await ctx.send("You do not have any Horrific Chests!")
                return
            inventory["horrific chest"] = inventory.get(
                "horrific chest", 0) - 1
            await pconn.execute(
                "UPDATE users SET inventory = $1::json where u_id = $2",
                inventory,
                ctx.author.id
            )
            reward = random.choices(
                ("legendchest", "boostedshiny", "gleam", "trick"),
                weights=(0.155, 0.3, 0.235, .31),
            )[0]
            if reward == "boostedshiny":
                pokemon = random.choice(await self.get_ghosts())
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True, shiny=True)
                msg = f"You received a shiny boosted IV {pokemon}!\n"
            elif reward == "gleam":
                pokemon = random.choice(self.HALLOWEEN_RADIANT)
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin='halloween', boosted=True)
                msg = f"<a:ExcitedChika:717510691703095386> **Congratulations! You received a boosted Halloween {pokemon}!**\n"
            elif reward == "missingno":
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["legend chest"] = inventory.get(
                    "legend chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                msg = "You received a Legend Chest!\n"
            elif reward == "trick":
                await ctx.send("*Trick or treat?*\nI choose trick!\n*A ghost flies out of the empty box*")
                return

        bones = random.randint(10, 15)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE halloween SET bone = bone + $1 WHERE u_id = $2", bones, ctx.author.id)
        msg += f"You also received {bones} <:mewbot_potion:1036332369076043776>!\n"
        await ctx.send(msg)

    # We removed this in 2022 Halloween event
    # @halloween.command(name="spread_ghosts")
    async def spread_ghosts(self, ctx):
        """Spread ghosts in this channel."""
        async with ctx.bot.db[0].acquire() as pconn:
            inv = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if not inv:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            honey = await pconn.fetchval(
                "SELECT * FROM honey WHERE channel = $1 LIMIT 1",
                ctx.channel.id,
            )
            if honey is not None:
                await ctx.send("There is already honey in this channel! You can't add more yet.")
                return
            if "ghost detector" in inv and inv["ghost detector"] >= 1:
                inv["ghost detector"] -= 1
                pass
            else:
                await ctx.send("You do not have any ghost detectors!")
                return
            expires = int(time.time() + (60 * 60))
            await pconn.execute(
                "INSERT INTO honey (channel, hour, owner, type) VALUES ($1, $2, $3, 'ghost')",
                ctx.channel.id,
                expires,
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                inv,
                ctx.author.id,
            )
            await ctx.send(
                f"You have successfully started a ghost detector, ghost spawn chances are greatly increased for the next hour!"
            )

    # @commands.hybrid_group()
    async def christmas(self, ctx):
        """Christmas commands."""
        pass

    # @christmas.command(name="spread_cheer")
    async def spread_cheer(self, ctx):
        """Spreads cheer (only matters if drops are live)"""
        # Drops, not commands, because cheer only matters when drops are live anyways
        if not self.CHRISTMAS_DROPS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            inv = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inv is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            honey = await pconn.fetchval(
                "SELECT * FROM honey WHERE channel = $1 LIMIT 1",
                ctx.channel.id,
            )
            if honey is not None:
                await ctx.send("There is already honey in this channel! You can't add more yet.")
                return
            if "holiday cheer" in inv and inv["holiday cheer"] >= 1:
                inv["holiday cheer"] -= 1
                pass
            else:
                await ctx.send("You do not have any holiday cheer, catch some pokemon to find some!")
                return
            expires = int(time.time() + (60 * 60))
            await pconn.execute(
                "INSERT INTO honey (channel, expires, owner, type) VALUES ($1, $2, $3, 'cheer')",
                ctx.channel.id,
                expires,
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE users SET holidayinv = $1::json WHERE u_id = $2",
                inv,
                ctx.author.id,
            )
            await ctx.send(
                f"You have successfully spread holiday cheer! Christmas spirits will be attracted to this channel for 1 hour."
            )

    # @christmas.command(name="buy")
    async def christmas_buy(self, ctx, option: int):
        """Buy something from the christmas shop."""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        if option < 1 or option > 5:
            await ctx.send("That isn't a valid option. Select a valid option from `/christmas shop`.")
            return
        async with self.bot.db[0].acquire() as pconn:
            holidayinv = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
            if "coal" not in holidayinv:
                await ctx.send("You haven't gotten any coal yet!")
                return
            if option == 1:
                if holidayinv["coal"] < 20:
                    await ctx.send("You don't have enough coal for that!")
                    return
                holidayinv["coal"] -= 20
                await pconn.execute("UPDATE users SET redeems = redeems + 1, holidayinv = $1::json WHERE u_id = $2", holidayinv, ctx.author.id)
                await ctx.send("You bought 1 redeem.")
            if option == 2:
                if holidayinv["coal"] < 50:
                    await ctx.send("You don't have enough coal for that!")
                    return
                holidayinv["coal"] -= 50
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["battle-multiplier"] = min(
                    inventory.get("battle-multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE users SET inventory = $1::json, holidayinv = $2::json WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 2x battle multipliers.")
            if option == 3:
                if holidayinv["coal"] < 50:
                    await ctx.send("You don't have enough coal for that!")
                    return
                holidayinv["coal"] -= 50
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["shiny-multiplier"] = min(
                    inventory.get("shiny-multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE users SET inventory = $1::json, holidayinv = $2::json WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 2x shiny multipliers.")
            if option == 4:
                if holidayinv["coal"] < 85:
                    await ctx.send("You don't have enough coal for that!")
                    return
                holidayinv["coal"] -= 85
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + 1
                await pconn.execute("UPDATE users SET inventory = $1::json, holidayinv = $2::json WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 1x radiant gem.")
            if option == 5:
                if holidayinv["coal"] < 200:
                    await ctx.send("You don't have enough coal for that!")
                    return
                holidayinv["coal"] -= 200
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "xmas" not in skins[pokemon]:
                    skins[pokemon]["xmas"] = 1
                else:
                    skins[pokemon]["xmas"] += 1
                await pconn.execute("UPDATE users SET skins = $1::json, holidayinv = $2::json WHERE u_id = $3", skins, holidayinv, ctx.author.id)
                await ctx.send(f"You got a {pokemon} christmas skin! Apply it with `/skin apply`.")

    # @christmas.command(name="inventory")
    async def christmas_inventory(self, ctx):
        """Check your christmas inventory."""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id
            )
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Christmas Inventory",
            color=random.choice(RED_GREEN),
        )
        if "coal" in inventory:
            embed.add_field(name="Coal", value=f"{inventory['coal']}x")
        if "small gift" in inventory:
            embed.add_field(name="Small Gift",
                            value=f"{inventory['small gift']}x")
        if "large gift" in inventory:
            embed.add_field(name="Large Gift",
                            value=f"{inventory['large gift']}x")
        if "holiday cheer" in inventory:
            embed.add_field(name="Holiday Cheer",
                            value=f"{inventory['holiday cheer']}x")

        embed.set_footer(
            text="Use /christmas shop to see what you can spend your coal on!")
        await ctx.send(embed=embed)

    # @christmas.command(name="shop")
    async def christmas_shop(self, ctx):
        """Check the christmas shop."""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        desc = (
            "**Option# | Price | Item**\n"
            "**1** | 20 coal | 1 redeem\n"
            "**2** | 50 coal | 2x battle multi\n"
            "**3** | 50 coal | 2x shiny multi\n"
            "**4** | 85 coal | 1 radiant gem\n"
            "**5** | 200 coal | Random christmas skin\n"
        )
        embed = discord.Embed(
            title="Christmas Shop",
            color=random.choice(RED_GREEN),
            description=desc,
        )
        embed.set_footer(
            text="Use /christmas buy with an option number to buy that item!")
        await ctx.send(embed=embed)

    # @christmas.command(name="open_smallgift")
    async def open_smallgift(self, ctx):
        """Open a small christmas gift."""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "small gift" not in inventory or inventory["small gift"] <= 0:
                await ctx.send("You do not have any small gifts!")
                return
            inventory["small gift"] = inventory.get("small gift", 0) - 1
            await pconn.execute(
                "UPDATE users SET holidayinv = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        reward = random.choices(
            ("skin", "coal", "redeem", "boostedice", "shinyice"),
            weights=(.04, 0.41, 0.15, 0.2, 0.1),
        )[0]
        if reward == "skin":
            async with ctx.bot.db[0].acquire() as pconn:
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "xmas" not in skins[pokemon]:
                    skins[pokemon]["xmas"] = 1
                else:
                    skins[pokemon]["xmas"] += 1
                await pconn.execute("UPDATE users SET skins = $1::json WHERE u_id = $2", skins, ctx.author.id)
            msg = (
                f"You opened the gift, and inside was a christmas skin for your {pokemon} to wear!\n"
                "Use `/skin apply` to apply it to a pokemon.\n"
            )
        elif reward == "coal":
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["coal"] = inventory.get("coal", 0) + 2
                await pconn.execute("UPDATE users SET holidayinv = $1::json WHERE u_id = $2", inventory, ctx.author.id)
            msg = "You opened the gift, and inside was 2 coal...\n"
        elif reward == "redeem":
            amount = 1
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = "You received 1 redeem!\n"
        elif reward == "boostedice":
            pokemon = random.choice(await self.get_ice())
            pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True)
            msg = f"You received a boosted IV {pokedata.emoji}{pokemon}!\n"
        elif reward == "shinyice":
            pokemon = random.choice(await self.get_ice())
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True)
            msg = f"You received a shiny {pokemon}!\n"
        elif reward == "raffle":
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute("UPDATE users SET raffle = raffle + 1 WHERE u_id = $1", ctx.author.id)
            msg = f"You were given an entry into the christmas raffle! The raffle will be drawn in the Mewbot official server.\n"
        await ctx.send(msg)

    # @christmas.command(name="open_largegift")
    async def open_largegift(self, ctx):
        """Open a large christmas gift."""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if "large gift" not in inventory or inventory["large gift"] <= 0:
                await ctx.send("You do not have any large gifts!")
                return
            inventory["large gift"] = inventory.get("large gift", 0) - 1
            await pconn.execute(
                "UPDATE users SET holidayinv = $1::json where u_id = $2",
                inventory,
                ctx.author.id,
            )
        reward = random.choices(
            ("skin", "coal", "redeem", "energy", "shinyice"),
            weights=(.1, 0.25, 0.6, 0.2, 0.01),
        )[0]
        if reward == "skin":
            async with ctx.bot.db[0].acquire() as pconn:
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "xmas" not in skins[pokemon]:
                    skins[pokemon]["xmas"] = 1
                else:
                    skins[pokemon]["xmas"] += 1
                await pconn.execute("UPDATE users SET skins = $1::json WHERE u_id = $2", skins, ctx.author.id)
            msg = (
                f"You opened the gift, and inside was a christmas skin for your {pokemon} to wear!\n"
                "Use `/skin apply` to apply it to a pokemon.\n"
            )
        elif reward == "coal":
            amount = random.randint(4, 5)
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["coal"] = inventory.get("coal", 0) + amount
                await pconn.execute("UPDATE users SET holidayinv = $1::json WHERE u_id = $2", inventory, ctx.author.id)
            msg = f"You opened the gift, and inside was {amount} coal...\n"
        elif reward == "redeem":
            amount = random.randint(1, 2)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} redeems!\n"
        elif reward == "energy":
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute("UPDATE users SET energy = energy + 2 WHERE u_id = $1", ctx.author.id)
            msg = "You found some eggnog in the gift, it restored some energy!\n"
        elif reward == "shinyice":
            pokemon = random.choice(await self.get_ice())
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True)
            msg = f"You received a shiny {pokemon}!\n"
        elif reward == "raffle":
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute("UPDATE users SET raffle = raffle + 1 WHERE u_id = $1", ctx.author.id)
            msg = f"You were given an entry into the christmas raffle! The raffle will be drawn in the Mewbot official server.\n"
        await ctx.send(msg)

    # @christmas.command(name="gift")
    @tradelock
    async def christmas_gift(self, ctx, amount: int):
        """Gift someone during christmas"""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        if amount <= 0:
            await ctx.send("You need to give at least 1 credit!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            if await pconn.fetchval("SELECT tradelock FROM users WHERE u_id = $1", ctx.author.id):
                await ctx.send("You are tradelocked, sorry")
                return
            curcreds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
            )
        if curcreds is None:
            await ctx.send(f"{ctx.author.name} has not started... Start with `/start` first!")
            return
        if amount > curcreds:
            await ctx.send("You don't have that many credits!")
            return
        if not await ConfirmView(ctx, f"Are you sure you want to donate {amount}<:mewcoin:1010959258638094386> to the christmas raffle prize pool?").wait():
            await ctx.send("Canceled")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            curcreds = await pconn.fetchval("SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id)
            if amount > curcreds:
                await ctx.send("You don't have that many credits anymore...")
                return
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                amount,
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = 920827966928326686",
                amount,
            )
            await ctx.send(
                f"{ctx.author.name} has donated {amount}<:mewcoin:1010959258638094386> to the christmas raffle prize pool"
            )
            await pconn.execute(
                "INSERT INTO trade_logs (sender, receiver, sender_credits, command, time) VALUES ($1, $2, $3, $4, $5) ",
                ctx.author.id, 920827966928326686, amount, "xmasgift", datetime.now()
            )

    @commands.hybrid_group()
    async def unown(self, ctx):
        """Unown commands"""
        pass

    @unown.command(name="guess")
    async def unown_guess(self, ctx, letter: str):
        """Guess the letter of an unown"""
        if self.UNOWN_WORD is None:
            await ctx.send("There is no active unown word!")
            return
        letter = letter.lower()
        if letter not in "abcdefghijklmnopqrstuvwxyz":
            await ctx.send("That is not an English letter!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            letters = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
        if letters is None:
            await ctx.send("You have not started yet.\nStart with `/start` first!")
            return
        if letters.get(letter, 0) <= 0:
            await ctx.send(f"You don't have any {self.UNOWN_CHARACTERS[1][letter]}s!")
            return
        letters[letter] -= 1
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE users SET holidayinv = $2::json WHERE u_id = $1", ctx.author.id, letters)
        for idx, character in enumerate(self.UNOWN_WORD):
            if character == letter and self.UNOWN_GUESSES[idx] is None:
                self.UNOWN_GUESSES[idx] = ctx.author.id
                break
        else:
            await ctx.send("That letter isn't in the word!")
            return
        # Successful guess
        await ctx.send("Correct! Added your letter to the board. You will be rewarded if the word is guessed.")
        await self.update_unown()

    @unown.command(name="inventory")
    async def unown_inventory(self, ctx):
        """Check your unown inventory"""
        async with ctx.bot.db[0].acquire() as pconn:
            letters = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
        if letters is None:
            await ctx.send("You have not started yet.\nStart with `/start` first!")
            return
        if not letters:
            await ctx.send("You haven't collected any unown yet. Go find some first!")
            return
        inv = ""
        for letter in "abcdefghijklmnopqrstuvwxyz":
            amount = letters.get(letter, 0)
            if amount > 0:
                inv += f"{self.UNOWN_CHARACTERS[1][letter]} - `{amount}`"
        embed = discord.Embed(
            title="Your unown",
            description=inv,
        )
        await ctx.send(embed=embed)

    @unown.command(name="start")
    @check_mod()
    async def unown_start(self, ctx, channel: discord.TextChannel, word: str):
        """Start the unown game"""
        if not await check_mod().predicate(ctx):
            await ctx.send("This command is only available to staff.")
            return
        if self.UNOWN_WORD:
            await ctx.send("There is already an active unown event!")
            return
        word = word.lower()
        if ''.join(c for c in word if c in 'abcdefghijklmnopqrstuvwxyz ') != word:
            await ctx.send("Word can only contain a-z and spaces!")
            return
        self.UNOWN_WORD = word
        self.UNOWN_GUESSES = [145519400223506432 if l ==
                              " " else None for l in word]
        self.UNOWN_MESSAGE = await channel.send(embed=discord.Embed(description="Setting up..."))
        await self.update_unown()
        await ctx.send("Event started!")

    async def give_egg(self, channel, user):
        """Gives a random egg to the provided user."""
        egg = random.choice(random.choices(
            self.EGGS, weights=(0.5, 0.3, 0.15, 0.05))[0])
        async with self.bot.db[0].acquire() as pconn:
            # yes this is bad, but it can only be a set of values so it's fiiiiiine
            await pconn.execute(f"INSERT INTO eggs (u_id, {egg}) VALUES ($1, 1) ON CONFLICT (u_id) DO UPDATE SET {egg} = eggs.{egg} + 1", user.id)
            """
            await pconn.execute("INSERT INTO eggs (u_id) VALUES ($1) ON CONFLICT DO NOTHING", user.id)
            await pconn.execute(f"UPDATE eggs SET {egg} = {egg} + 1 WHERE u_id = $1", user.id)
            """
        await channel.send(f"The pokemon was holding a {egg} easter egg!\nUse command `/easter list` to view your eggs.")

    async def give_candy(self, channel, user):
        """Gives candy to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute("INSERT INTO halloween (u_id) VALUES ($1) ON CONFLICT DO NOTHING", user.id)
            await pconn.execute("UPDATE halloween SET candy = candy + $1 WHERE u_id = $2", random.randint(2, 5), user.id)
        await channel.send(f"The pokemon dropped some candy!\nUse command `/halloween inventory` to view what you have collected.")

    async def give_bone(self, channel, user):
        """Gives potions to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute("INSERT INTO halloween (u_id) VALUES ($1) ON CONFLICT DO NOTHING", user.id)
            await pconn.execute("UPDATE halloween SET bone = bone + $1 WHERE u_id = $2", random.randint(1, 3), user.id)
        await channel.send(f"The pokemon dropped some potions!\nUse command `/halloween inventory` to view what you have collected.")

    async def give_scary_mask(self, channel, user):
        """Gives jack-o-laterns to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute("INSERT INTO halloween (u_id) VALUES ($1) ON CONFLICT DO NOTHING", user.id)
            await pconn.execute("UPDATE halloween SET pumpkin = pumpkin + $1 WHERE u_id = $2", random.randint(1, 2), user.id)
        await channel.send(f"The pokemon dropped a scary mask!\nUse command `/halloween inventory` to view what you have collected.")

    async def get_ghosts(self):
        data = await self.bot.db[1].ptypes.find({"types": 8}).to_list(None)
        data = [x["id"] for x in data]
        data = await self.bot.db[1].forms.find({"pokemon_id": {"$in": data}}).to_list(None)
        data = [x["identifier"].title() for x in data]
        return list(set(data) & set(totalList))

    async def get_ice(self):
        data = await self.bot.db[1].ptypes.find({"types": 15}).to_list(None)
        data = [x["id"] for x in data]
        data = await self.bot.db[1].forms.find({"pokemon_id": {"$in": data}}).to_list(None)
        data = [x["identifier"].title() for x in data]
        return list(set(data) & set(totalList))

    async def give_cheer(self, channel, user):
        async with self.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", user.id
            )
            inventory["holiday cheer"] = inventory.get("holiday cheer", 0) + 1
            await pconn.execute(
                "UPDATE users SET holidayinv = $1::json where u_id = $2",
                inventory,
                user.id,
            )
        await channel.send(f"The pokemon dropped some holiday cheer!\nUse command `/spread cheer` to share it with the rest of the server.")

    async def maybe_spawn_christmas(self, channel):
        # Not sure why this is here
        # async with self.bot.db[0].acquire() as pconn:
        # honey = await pconn.fetchval(
        #"SELECT type FROM honey WHERE channel = $1 LIMIT 1",
        # channel.id,
        # )
        # if honey != "cheer":
        # return
        await asyncio.sleep(random.randint(30, 60))
        await ChristmasSpawn(self, channel, random.choice(list(self.CHRISTMAS_MOVES.keys()))).start()

    async def maybe_spawn_unown(self, channel):
        if not self.UNOWN_MESSAGE:
            return
        if channel.guild.id != int(os.environ["OFFICIAL_SERVER"]):
            return
        word = random.choice(self.UNOWN_WORDLIST).strip()
        index = random.randrange(len(word))
        letter = word[index]
        formatted = ""
        for idx, character in enumerate(word):
            formatted += self.UNOWN_CHARACTERS[idx == index][character]
        embed = discord.Embed(
            title="Unown are gathering, quickly repeat the word they are forming to catch one!",
            description=formatted,
        )
        message = await channel.send(embed=embed)
        try:
            winner = await self.bot.wait_for(
                "message",
                check=lambda m: m.channel == channel and m.content.lower().replace(
                    f"<@{self.bot.user.id}>", "").replace(" ", "", 1) == word,
                timeout=60
            )
        except asyncio.TimeoutError:
            await message.delete()
            return

        async with self.bot.db[0].acquire() as pconn:
            letters = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", winner.author.id)
            if letters is not None:
                letters[letter] = letters.get(letter, 0) + 1
                await pconn.execute("UPDATE users SET holidayinv = $2::json WHERE u_id = $1", winner.author.id, letters)

        embed = discord.Embed(
            title="Guessed!",
            description=f"{winner.author.mention} received a {self.UNOWN_CHARACTERS[1][letter]}",
        )
        await message.edit(embed=embed)

    async def update_unown(self):
        if not self.UNOWN_MESSAGE:
            return
        formatted = ""
        for idx, character in enumerate(self.UNOWN_WORD):
            if character == " ":
                formatted += " \| "
            elif self.UNOWN_GUESSES[idx] is not None:
                formatted += self.UNOWN_CHARACTERS[1][character]
            else:
                formatted += " \_ "
        if all(self.UNOWN_GUESSES):
            winners = defaultdict(int)
            for idx, character in enumerate(self.UNOWN_WORD):
                if character != " ":
                    winners[self.UNOWN_GUESSES[idx]
                            ] += self.UNOWN_POINTS[character]
            async with self.bot.db[0].acquire() as pconn:
                for uid, points in winners.items():
                    if points > 10:
                        points //= 10
                        inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", uid)
                        inventory["rare chest"] = inventory.get(
                            "rare chest", 0) + points
                        await pconn.execute("UPDATE users SET inventory = $1::json WHERE u_id = $2", inventory, uid)
                        points = 10
                    await pconn.execute("UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2", points * 5000, uid)
                await pconn.execute("UPDATE users SET holidayinv = '{}'")
            embed = discord.Embed(
                title="You identified the word!",
                description=(
                    f"{formatted}\n\n"
                    "Users who guessed a letter correctly have been given credits.\n"
                )
                # TODO: change to what the reward actually is?
            )
            await self.UNOWN_MESSAGE.edit(embed=embed)
            self.UNOWN_WORD = None
            self.UNOWN_GUESSES = []
            self.UNOWN_MESSAGE = None
            return
        embed = discord.Embed(
            title="Guess the unown word!",
            description=(
                f"{formatted}\n\n"
                "Collect unown letters by identifying unown words in this server.\n"
                "Check what letters you have with `/unown inventory`.\n"
                "Guess with one of your letters using `/unown guess <letter>`.\n"
                "When the word is identified, all users who guess a letter correctly get a reward!\n"
            )
        )
        await self.UNOWN_MESSAGE.edit(embed=embed)

    @commands.Cog.listener()
    async def on_poke_spawn(self, channel, user):
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS and not random.randrange(20):
            await self.give_egg(channel, user)
        if self.HALLOWEEN_DROPS:
            if not random.randrange(30):
                await self.give_candy(channel, user)
            if not random.randrange(10):
                await self.maybe_spawn_christmas(channel)
        if self.CHRISTMAS_DROPS:
            if not random.randrange(30):
                await self.give_cheer(channel, user)
            if not random.randrange(10):
                await self.maybe_spawn_christmas(channel)
        if not random.randrange(10):
            await self.maybe_spawn_unown(channel)

    @commands.Cog.listener()
    async def on_poke_fish(self, channel, user):
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS and not random.randrange(5):
            await self.give_egg(channel, user)
        if self.HALLOWEEN_DROPS:
            if not random.randrange(100):
                await self.give_scary_mask(channel, user)
            elif not random.randrange(15):
                await self.give_bone(channel, user)
            elif not random.randrange(4):
                await self.give_candy(channel, user)
        if not random.randrange(5):
            await self.maybe_spawn_unown(channel)

    @commands.Cog.listener()
    async def on_poke_breed(self, channel, user):
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS and not random.randrange(18):
            await self.give_egg(channel, user)
        if self.HALLOWEEN_DROPS:
            if not random.randrange(200):
                await self.give_scary_mask(channel, user)
            elif not random.randrange(25):
                await self.give_bone(channel, user)
            elif not random.randrange(4):
                await self.give_candy(channel, user)
        if not random.randrange(7):
            await self.maybe_spawn_unown(channel)


class ChristmasSpawn(discord.ui.View):
    """A spawn embed for a christmas spawn."""

    def __init__(self, cog, channel, poke: str):
        super().__init__(timeout=140)
        self.cog = cog
        self.channel = channel
        self.poke = poke
        self.registered = []
        self.attacked = {}
        self.state = "registering"
        self.message = None

    async def interaction_check(self, interaction):
        if self.state == "registering":
            if interaction.user in self.registered:
                await interaction.response.send_message(content="You have already joined!", ephemeral=True)
                return False
            self.registered.append(interaction.user)
            await interaction.response.send_message(content="You have joined the battle!", ephemeral=True)
            return False
        elif self.state == "attacking":
            if interaction.user in self.attacked:
                await interaction.response.send_message(content="You have already attacked!", ephemeral=True)
                return False
            if interaction.user not in self.registered:
                await interaction.response.send_message(content="You didn't join the battle! You can't attack this one.", ephemeral=True)
                return False
            return True
        else:
            await interaction.response.send_message(content="This battle has already ended!", ephemeral=True)
            return False
        return False

    async def start(self):
        pokeurl = "http://dyleee.github.io/mewbot-images/sprites/" + await get_file_name(self.poke, self.cog.bot, skin="halloween")
        guild = await self.cog.bot.mongo_find("guilds", {"id": self.channel.guild.id})
        if guild is None:
            small_images = False
        else:
            small_images = guild["small_images"]
        color = random.choice(RED_GREEN)
        self.embed = discord.Embed(
            title="A Halloween Pokémon has spawned, join the fight to take it down!",
            color=color,
        )
        self.embed.add_field(name="-", value="Click the button to join!")
        if small_images:
            self.embed.set_thumbnail(url=pokeurl)
        else:
            self.embed.set_image(url=pokeurl)
        self.add_item(discord.ui.Button(
            label="Join", style=discord.ButtonStyle.green))
        self.message = await self.channel.send(embed=self.embed, view=self)
        await asyncio.sleep(10)
        self.clear_items()
        moves = []
        for idx, move in enumerate(self.cog.CHRISTMAS_MOVES[self.poke]):
            damage = max(2 - idx, 0)
            moves.append(ChristmasMove(move, damage))
        random.shuffle(moves)
        for move in moves:
            self.add_item(move)
        self.max_hp = int(len(self.registered) * 1.33)
        self.embed = discord.Embed(
            title="A Halloween Pokémon has spawned, attack it with everything you've got!",
            color=color,
        )
        self.embed.add_field(
            name="-", value=f"HP = {self.max_hp}/{self.max_hp}")
        if small_images:
            self.embed.set_thumbnail(url=pokeurl)
        else:
            self.embed.set_image(url=pokeurl)
        self.state = "attacking"
        await self.message.edit(embed=self.embed, view=self)
        for i in range(5):
            await asyncio.sleep(3)
            hp = max(self.max_hp - sum(self.attacked.values()), 0)
            self.embed.clear_fields()
            self.embed.add_field(name="-", value=f"HP = {hp}/{self.max_hp}")
            await self.message.edit(embed=self.embed)
        self.state = "ended"
        hp = max(self.max_hp - sum(self.attacked.values()), 0)
        if hp > 0:
            self.embed = discord.Embed(
                title="The Halloween Pokémon got away!",
                color=color,
            )
            hp = max(self.max_hp - sum(self.attacked.values()), 0)
            self.embed.add_field(name="-", value=f"HP = {hp}/{self.max_hp}")
            if small_images:
                self.embed.set_thumbnail(url=pokeurl)
            else:
                self.embed.set_image(url=pokeurl)
            await self.message.edit(embed=self.embed, view=None)
            return
        async with self.cog.bot.db[0].acquire() as pconn:
            # This would be for Christmas rewards
            # for attacker, damage in self.attacked.items():
            # inventory = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", attacker.id)
            # if inventory is None:
            # continue
            # if damage == 2:
            #inventory["large gift"] = inventory.get("large gift", 0) + 1
            # elif damage == 1:
            #inventory["small gift"] = inventory.get("small gift", 0) + 1
            # elif damage == 0:
            #inventory["coal"] = inventory.get("coal", 0) + 1
            # await pconn.execute("UPDATE users SET holidayinv = $1::json WHERE u_id = $2", inventory, attacker.id)
            # This is for halloween event
            for attacker, damage in self.attacked.items():
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", attacker.id
                )
                if inventory is None:
                    continue
                if damage == 2:
                    inventory["fleshy chest"] = inventory.get(
                        "fleshy chest", 0) + 1
                elif damage == 1:
                    inventory["spooky chest"] = inventory.get(
                        "spooky chest", 0) + 1
                elif damage == 0:
                    await pconn.execute("UPDATE halloween SET candy = candy + $1 WHERE u_id = $2", random.randint(2, 5), attacker.id)
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    attacker.id,
                )
        self.embed = discord.Embed(
            title="The Halloween Pokémon was defeated! Attackers have been awarded.",
            color=color,
        )
        if small_images:
            self.embed.set_thumbnail(url=pokeurl)
        else:
            self.embed.set_image(url=pokeurl)
        await self.message.edit(embed=self.embed, view=None)


class ChristmasMove(discord.ui.Button):
    """A move button for attacking a christmas pokemon."""

    def __init__(self, move, damage):
        super().__init__(
            label=move,
            style=random.choice(
                [discord.ButtonStyle.red, discord.ButtonStyle.green]),
        )
        self.move = move
        self.damage = damage
        if damage == 2:
            self.effective = "It's super effective! You will get a Fleshy Chest if the poke is defeated."
        elif damage == 1:
            self.effective = "It's not very effective... You will get a Spooky Chest if the poke is defeated."
        else:
            self.effective = "It had no effect... You will only get candy if the poke is defeated."

    async def callback(self, interaction):
        self.view.attacked[interaction.user] = self.damage
        await interaction.response.send_message(content=f"You used {self.move}. {self.effective}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Events(bot))
