import os
import discord
import random
import asyncio
import time

from unicodedata import name
from discord.ext import commands
from mewcogs.pokemon_list import *
from mewutils.checks import tradelock, check_mod
from mewutils.misc import get_file_name, get_emoji, ConfirmView
from collections import defaultdict
from datetime import datetime
from typing import Literal
from dataclasses import dataclass

ORANGE = 0xF4831B
RED_GREEN = [0xBB2528, 0x146B3A]

@dataclass
class Pokemon:
    name: str
    gender: str
    hp: int
    attack: int
    defense: int
    spatk: int
    spdef: int
    speed: int
    level: int
    shiny: bool
    held_item: str
    happiness: int
    ability_id: int
    ab_ids: list
    nature: str

    def is_a_form(self):
        return is_formed(self.name)

    def is_a_regional_form(self):
        return any(
            self.name.endswith(form) for form in ["alola", "galar", "hisui", "paldea"]
        )

#Here for Easter 2023 Event
async def get_egg(ctx, fund):
    shiny = False
    boosted = False
    #Proceed to generate egg and add to user
    max_chance = 28000 - fund
    special_chance = random.randint(1, max_chance)

    #5. Boosted Legendary, 5% Shiny
    if special_chance <= 2500: #10%
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (ubList, LegendList),
            weights=(.7, .3),
        )[0]
        poke_name = random.choice(choiceList)
    
    #4. Boosted 80% UB/ 20% Legendary, 10% Shiny
    elif special_chance <= 5000: 
        if (random.randint(1, 100)) <= 10: 
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pseudoList, ubList, LegendList),
            weights=(.4, .4, .2),
        )[0]
        poke_name = random.choice(choiceList)
    
    #3. 40% Boosted Psu, 25% Shiny
    elif special_chance <= 10000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pseudoList, ubList),
            weights=(.9, .1),
        )[0]
        poke_name = random.choice(choiceList)
    
    #2. 60% Boosted Starter/Pokemon, 75% Shiny
    elif special_chance <= 15000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pList, starterList, pseudoList),
            weights=(.5, .4, .1),
        )[0]
        poke_name = random.choice(choiceList) 
    
    #1. Boosted Starter or Pseudo, 80% Shiny
    elif special_chance <= 24000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pList, starterList),
            weights=(.8, .2),
        )[0]
        poke_name = random.choice(choiceList)
    
    #Boosted Normal Pokemon, 80% Shiny (Edge Case)
    else:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        poke_name = random.choice(pList)

    #Generate Egg Stats
    #IVs and Nature
    min_iv = 13 if boosted else 1
    max_iv = 31 if boosted or random.randint(0, 1) else 29
    hpiv = random.randint(min_iv, max_iv)
    atkiv = random.randint(min_iv, max_iv)
    defiv = random.randint(min_iv, max_iv)
    spaiv = random.randint(min_iv, max_iv)
    spdiv = random.randint(min_iv, max_iv)
    speiv = random.randint(min_iv, max_iv)
    nature = random.choice(natlist)

    #Everything else
    form_info = await ctx.bot.db[1].forms.find_one({"identifier": poke_name.lower()})
    pokemon_info = await ctx.bot.db[1].pfile.find_one({"id": form_info["pokemon_id"]})
    try:
        gender_rate = pokemon_info["gender_rate"]
    except Exception:
        ctx.logger.warn("No Gender Rate for %s" % pokemon_info["identifier"])
        return None

    ab_ids = (
        await ctx.bot.db[1]
        .poke_abilities.find({"pokemon_id": form_info["pokemon_id"]})
        .to_list(length=3)
    )
    ab_ids = [doc["ability_id"] for doc in ab_ids]

    #Gender
    if "idoran-" in poke_name:
        gender = poke_name[-2:]
    elif poke_name.lower() == "illumise":
        gender = "-f"
    elif poke_name.lower() == "volbeat":
        gender = "-m"
    # -1 = genderless pokemon
    elif gender_rate == -1:
        gender = "-x"
    # 0 = male only, 8 = female only, in between means mix at that ratio.
    # 0 < 0 = False, so the poke will always be male
    # 7 < 8 = True, so the poke will always be female
    elif random.randrange(8) < gender_rate:
        gender = "-f"
    else:
        gender = "-m"

    emoji = get_emoji(
        shiny=shiny,
    )
    p = Pokemon(
        poke_name.capitalize(),
        gender,
        hpiv,
        atkiv,
        defiv,
        spaiv,
        spdiv,
        speiv,
        1,
        shiny,
        "None",
        0,
        random.randrange(len(ab_ids)),
        ab_ids,
        nature,
    )
    return p, emoji, boosted

#Here for Easter 2023 Event
def get_insert_query(ctx, poke, is_shadow=False):
    tackle = "tackle"
    query2 = """
    INSERT INTO pokes (pokname, hpiv, atkiv, defiv, spatkiv, spdefiv, speediv, hpev, atkev, defev, spatkev, spdefev, speedev, pokelevel, moves, hitem, exp, nature, expcap, poknick, price, market_enlist, happiness, fav, ability_index, counter, name, gender, caught_by, shiny, skin)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31) RETURNING id"""
    skin = "shadow" if is_shadow else None
    args = (
        "Egg",
        poke.hp,
        poke.attack,
        poke.defense,
        poke.spatk,
        poke.spdef,
        poke.speed,
        0,
        0,
        0,
        0,
        0,
        0,
        5,
        [tackle, tackle, tackle, tackle],
        "None",
        1,
        poke.nature,
        35,
        "None",
        0,
        False,
        0,
        False,
        poke.ability_id,
        150,
        poke.name,
        poke.gender,
        ctx.author.id,
        poke.shiny,
        skin
    )
    return query2, args


class Events(commands.Cog):
    """Various seasonal events in Mewbot."""

    def __init__(self, bot):
        self.bot = bot
        # Seasonal toggles
        self.EASTER_DROPS = False
        self.EASTER_COMMANDS = True
        self.HALLOWEEN_DROPS = False
        self.HALLOWEEN_COMMANDS = False
        self.CHRISTMAS_DROPS = False
        self.CHRISTMAS_COMMANDS = False
        self.CHRISTMAS_DROPS = False
        self.VALENTINE_DROPS = False
        self.VALENTINE_COMMANDS = False
        self.SUMMER_DROPS = True
        self.SUMMER_COMMANDS = True
        self.HALLOWEEN_RADIANT = [
            'Absol',
            'Litwick',
            'Gligar',
            'Misdreavus',
            'Yamper',
            'Togepi',
            'Marshadow',
            'Shroomish',
            'Hatenna',
        ]
        # "Poke name": ["Super effective (2)", "Not very (1)", "No effect (0)", "No effect (0)"]
        self.CHRISTMAS_MOVES = {
            'Arceus': ["Close Combat","Tackle", "Shadow Claw","Shadow Sneak"],
            'Charizard': ["Rock slide","Solar Beam","Will O Wisp","Howl"],
            'Caterpie': ["Flame Burst","Sand Tomb","Quiver Dance","Poison Powder"],
            'Diglett': ["Water Shuriken","Rock Slide","Growl","Sleep Powder"],
            'Mew': ["Dark Pulse", "Extrasensory", "Block", "Gravity"],
            'Miltank': ["Close Combat", "Echoed Voice", "Healing Wish", "Sandstorm"],
            'Torchic': ["Dive","Pyro Ball","Toxic","Sunny Day"],
            "Gardevoir": ["Shadow Ball","Earthquake","Magic Room","Recover"],
            'Manaphy': ["Leaf Blade", "Ice Beam", "Helping Hand", "Reflect"],
            'Victini': ["Dark Pulse","Psychic","Will O Wisp","Toxic"],
            'Dedenne': ["Earthquake","Close Combat","Outrage,","Dragon Tail"],
            'Carbink': ["Metal Claw","Psychic","Dragon Claw","Scale Shot"],
            'Pheromosa': ["Ember","Axe Kick","Mat Block","Protect"],
            'Lunala': ["Poltergeist","Moonblast","Bulk up","Tackle"],
            'Mimikyu': ["Moongeist Beam","Belch","Outrage","Shadow Sneak"],
            'Scorbunny': ["Snipe Shot","Grassy Glide","Court Change","Taunt"],
            'Raboot': ["Snipe Shot","Grassy Glide","Court Change","Taunt"],         
        }
        self.EVENT_POKEMON = [
            'Wooper',
            'Quagsire',
            'Machamp',
            'Sawk',
            'Zarude',
            'Meloetta',
            'Buzzwole',
            'Mimikyu',
            'Pheromosa',
            'Azurill',
            'Petilil',
        ]
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
        self.start_purchaselock = []
        try:
            with open(self.bot.app_directory / "shared" / "data" / "wordlist.txt") as f:
                self.UNOWN_WORDLIST = f.readlines().copy()
        except Exception:
            pass

    #@commands.hybrid_group()
    async def easter(self, ctx: commands.Context):
        ...

    #@easter.command(name="info")
    async def easter_info(self, ctx):
        embed = discord.Embed(
            title="Mewbot Easter Event 2023",
            description="More details on the event and how things are working!",
            color=0x00FF00
        )
        embed.add_field(
            name="Raids",
            value="Raids have a chance of spawning after a Pokemon is caught in your server. Nothing special needs to be done to active them and they drop 🥕",
            inline=True
        )
        embed.add_field(
            name="Shop and Carrots 🥕",
            value="There is a shop that offers bot wide benefits. Uses 🥕 as currency. They can be earned with Raids or as a drop during Breeding",
            inline=True
        )
        embed.add_field(
            name="Event Skins",
            value="In the shop for the duration of the event. Can be assigned to any Pokemon the skin belongs too.",
            inline=True
        )
        embed.add_field(
            name="Winter Fund and Eggs",
            value=(
                "The Easter Bunny has provided us with the opportunity to gain **Painted Eggs**. They are available in the shop for 50 🥕."
                "The Winter Fund is the Easter Bunny's storage for the Winter! By increasing your fund, Diggersby is more likely to give you a Boosted and/or Shiny Egg"
                "These eggs can be **any** Pokemon from the bot! As you donate more the choice of Pokemon your egg can be gets better and better"
            ),
            inline=False
        )
        await ctx.send(embed=embed)

    #@easter.command(name="shop")
    async def easter_shop(self, ctx):
        """Check the easter shop."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the Easter Season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            try:
                dets = await pconn.fetchrow(
                    "SELECT carrots, easter_fund FROM events_new WHERE u_id = $1",
                    ctx.author.id
                )
            except:
                dets = None

            if dets is None:
                carrots = 0
                fund = 0
            else:
                carrots = dets['carrots']
                fund = dets['easter_fund']

        embed = discord.Embed(
            title="Easter Shop",
            description=f"Event details can be found with `/easter info`.\nBuy with `/easter buy`\n`Carrots`: {carrots:,} - `Winter Fund`: {fund:,}/25,000",
            color=0x00FF00,
        )
        embed.add_field(
            name="General <a:radiantgem:774866137472827432>",
            value="1-25 Gleam <a:radiantgem:774866137472827432>\n75 🥕\nEaster Skin\n150 🥕",
            inline=True
        )
        embed.add_field(
            name="Multipliers ",
            value="2x Battle Multi ⏫\n50 🥕\n2x Shiny Multi ⏫\n50 🥕",
            inline=True
        )
        embed.add_field(
            name="Eggs <:poke_egg:676810968000495633>",
            value="Egg and Redeem\n50 🥕\nEgg and Fund Increase\n150 🥕",
            inline=True
        )
        embed.set_thumbnail(
            url="https://dyleee.github.io/mewbot-images/diggersby.png"
        )
        embed.set_footer(
            text="Diggersby Image made by @Ort.Homeless on Instagram!")
        await ctx.send(embed=embed)


    #@easter.command(name="buy")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def easter_buy(self, ctx, option: Literal["Gleam Gems", "Easter Skin", "Battle Mult.", "Shiny Mult.", "Fund", "Painted Egg"]):
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the Easter Season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            try:
                dets = await pconn.fetchrow(
                    "SELECT carrots, easter_fund FROM events_new WHERE u_id = $1", 
                    ctx.author.id
                )
            except:
                dets = None
            if dets is None:
                await ctx.send("You don't have any Easter 🥕 to spend yet!")
                return
            
            carrots : int = dets['carrots']
            easter_fund = dets['easter_fund']
            give_egg = False

            #Gleam Gems
            if option == "Gleam Gems":
                amount = random.randint(1, 25)
                if (carrots - 75) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 75
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", 
                    ctx.author.id
                )
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + amount
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json WHERE u_id = $2", 
                    inventory, 
                    ctx.author.id
                )
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id
                )
                await ctx.send(f"You gained {amount} <a:radiantgem:774866137472827432> Gleam Gems!")
                return
            #Battle Multiplier
            if option == "Battle Mult.":
                if (carrots - 50) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 50
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", 
                    ctx.author.id
                )
                inventory["battle-multiplier"] = min(
                    inventory.get("battle-multiplier", 0) + 2, 50
                )
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json WHERE u_id = $2", 
                    inventory, 
                    ctx.author.id
                )
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id
                )
                await ctx.send(f"You bought 2x Battle Multipliers.")
            #Shiny Multiplier
            if option == "Shiny Mult.":
                if (carrots - 50) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 50
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", 
                    ctx.author.id
                )
                inventory["shiny-multiplier"] = min(
                    inventory.get("shiny-multiplier", 0) + 2, 50
                )
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json WHERE u_id = $2", 
                    inventory, 
                    ctx.author.id
                )
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id
                )
                await ctx.send(f"You bought 2x Shiny Multipliers.")
            #Skin
            if option == "Easter Skin":
                if (carrots - 150) < 0:
                    await ctx.send("You don't have enough 🥕 carrots for that!")
                    return
                carrots -= 150
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots, ctx.author.id
                )
                skins = await pconn.fetchval(
                    "SELECT skins::json FROM users WHERE u_id = $1", 
                    ctx.author.id
                )
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "easter2023" not in skins[pokemon]:
                    skins[pokemon]["easter2023"] = 1
                else:
                    skins[pokemon]["easter2023"] += 1
                await pconn.execute(
                    "UPDATE users SET skins = $1::json WHERE u_id = $2", 
                    skins, 
                    ctx.author.id
                )
                await ctx.send(f"You got a {pokemon.title()} Easter skin! Apply it with `/skin apply`.")
            #Fund
            if option == "Fund":
                if (carrots - 150) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                if easter_fund >= 25000:
                    await ctx.send("Congrats! You've maxed out your fund!\nPlease use `/easter buy option: Painted Egg` instead!!")
                    return
                if (easter_fund + 150) > 25000:
                    charge = 25000 - easter_fund
                    carrots -= charge
                    bonus_msg = f"\nYou've successfully added **{charge}** 🥕 to the Winter Fund, it is now Maxed!!"
                else:
                    charge = 150
                    carrots -= 150
                    bonus_msg = "\nYou've successfully added **150** 🥕 to the Winter Fund!"
                await pconn.execute(
                    "UPDATE events_new SET easter_fund = easter_fund + $1, carrots = $2 WHERE u_id = $3",
                    charge,
                    carrots,
                    ctx.author.id
                )
                give_egg = True
            #Painted Egg   
            if option == "Painted Egg":
                if (carrots - 50) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 50
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + 1 WHERE u_id = $1",
                    ctx.author.id
                )
                bonus_msg = "\nAlso gained **1 Redeem**!"
                give_egg = True
            
            if give_egg:
                #Check daycare
                pokes = await pconn.fetchrow(
                    "SELECT pokes, daycarelimit FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                dlimit = pokes["daycarelimit"]
                pokes = pokes["pokes"]
                daycared = await pconn.fetchval(
                    "SELECT count(*) FROM pokes WHERE id = ANY ($1) AND pokname = 'Egg'",
                    pokes,
                )
                if daycared > dlimit:
                    await ctx.send("You already have enough Pokemon in the Daycare!\nIncrease space with `/buy daycare`")
                    return
                
                #Remove carrots
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id
                )
                
                egg, emoji, boosted = await get_egg(ctx, easter_fund)
                query, args = get_insert_query(ctx, egg)

                async with ctx.bot.db[0].acquire() as pconn:
                    pokeid = await pconn.fetchval(query, *args)
                    await pconn.execute(
                        "UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2",
                        pokeid,
                        ctx.author.id,
                    )
                ivsum = (
                    egg.attack
                    + egg.defense
                    + egg.spatk
                    + egg.spdef
                    + egg.speed
                    + egg.hp
                )
                ivpercent = round((ivsum / 186) * 100, 2)
                if boosted:
                    msg = "Boosted"
                else:
                    msg = ""
                embed = discord.Embed(
                    title=f"{ctx.author}'s Painted Egg",
                    description=f"It's been automatically added to your Pokemon list!{bonus_msg}",
                    color=0x00FF00
                )
                embed.add_field(
                    name="Egg Details",
                    value=f"Diggersby has granted you a {emoji} {msg} **{ivpercent}** Painted Egg!\nIt'll hatch in **150** steps!"
                )
                embed.set_image(
                    url = "https://dyleee.github.io/mewbot-images/eastereggs.png"
                )
                embed.set_footer(
                    text="Easter 2023 ends on 4/23 | Make sure to join Mewbot Official for more Events!"
                )
                await ctx.send(embed=embed)


    #@easter.command(name="convert")
    async def easter_convert(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            old_dets = await pconn.fetchrow(
                "SELECT * FROM events WHERE u_id = $1 ORDER BY easter_fund DESC LIMIT 1",
                ctx.author.id
            )
            converted = old_dets['converted']
            if converted:
                await ctx.send("Sorry you've done this already!")
                return
                
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                ctx.author.id
            )
            await pconn.execute(
                f"UPDATE events_new SET carrots = carrots + $1 WHERE u_id = $2", 
                old_dets['carrots'],
                ctx.author.id
            )
            await pconn.execute(
                f"UPDATE events_new SET easter_fund = easter_fund + $1 WHERE u_id = $2",
                old_dets['easter_fund'],
                ctx.author.id
            )
            await pconn.execute(
                "UPDATE events SET converted = True WHERE u_id = $1",
                ctx.author.id
            )
            await ctx.send("Successful")

    @commands.hybrid_group()
    async def summer(self, ctx: commands.Context):
        ...

    @summer.command(name="shop")
    async def summer_shop(self, ctx):
        """Check the summer shop."""
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the Summer Season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            try:
                event_data = await pconn.fetchrow(
                    "SELECT milk, event_limit FROM events_new WHERE u_id = $1",
                    ctx.author.id
                )
                raffle_count = await pconn.fetchval(
                    "SELECT raffle FROM users WHERE u_id = $1",
                    ctx.author.id
                )
                milk_count = event_data['milk']
                event_limit = event_data['event_limit']
            except:
                milk_count = 0
                event_limit = 0
                raffle_count = 0

            if event_limit >= 100:
                event_limit = 100

        embed = discord.Embed(
            title="Summer Shop",
            description=(
                f"Use Cups of Milk 🥛 gained from Raids to purchase items."
                f"\nYou have **{milk_count:,}** 🥛"
            ),
            color=0xFFFFFF,
        )
        embed.add_field(
            name="Currency",
            value=(
                f"`1.` 2-3 Redeems <:redeem:1037942226132668417>\n**Cost**: 50 🥛 - **Limit**: {event_limit}/100"
                "\n`2.` 1-25 Gleam Gems <a:radiantgem:774866137472827432>\n**Cost**: 75 🥛"
            ),
            inline=False
        )
        embed.add_field(
            name="Multipliers",
            value=(
                "`3.` 2x Battle Multi ⏫\n**Cost**: 50 🥛"
                "\n`4.` 2x Shiny Multi ⏫\n**Cost**: 50 🥛"
            ),
            inline=False
        )
        embed.add_field(
            name="Misc",
            value=(
                f"`5.` 1 Raffle Entry\n**Cost**: 100 🥛 - **Entries**: {raffle_count}"
                "\n`6.` Random Summer Skin\n**Cost**: 100 🥛"
            ),
            inline=False
        )
        embed.set_thumbnail(
            url="https://archives.bulbagarden.net/media/upload/thumb/9/91/Moomoo_Milk_anime.png/800px-Moomoo_Milk_anime.png"
        )
        embed.set_footer(
            text="Use /summer buy with an option number to buy that item!")
        await ctx.send(embed=embed)

    @summer.command(name="buy")
    async def summer_buy(self, ctx, option:int):
        """Buy an item from the summer event shop"""
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the summer season!")
            return
        #User can't participate in event
        #if ctx.author.id == 1075429458271547523:
            #return
        if option < 1 or option > 6:
            await ctx.send("That isn't a valid option. Select a valid option from `/summer shop`.")
            return
        if ctx.author.id in self.start_purchaselock:
            await ctx.send("Sorry, finish any pending purchases first.")
            return
        self.start_purchaselock.append(ctx.author.id)

        async with self.bot.db[0].acquire() as pconn:
            event_data = await pconn.fetchrow("SELECT milk, event_limit FROM events_new WHERE u_id = $1", ctx.author.id)
            milk = event_data['milk']
            limit = event_data['event_limit']

            if milk == 0:
                await ctx.send("You haven't gotten any 🥛 yet!")
                return
            
            if option == 1:
                if limit >= 100:
                    await ctx.send("You've reached the daily purchase limit.")
                    self.start_purchaselock.remove(ctx.author.id)
                    return

                if milk < 50:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                
                milk -= 50
                redeem_amount = random.randint(2, 3)
                await pconn.execute("UPDATE users SET redeems = redeems + $1 WHERE u_id = $2", redeem_amount, ctx.author.id)
                await pconn.execute("UPDATE events_new SET milk = $1, event_limit = event_limit + $2 WHERE u_id = $3", milk, redeem_amount, ctx.author.id)
                await ctx.send(f"You bought {redeem_amount} Redeems.")
                self.start_purchaselock.remove(ctx.author.id)

            if option == 2:
                amount = random.randint(1, 25)
                if milk < 75:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                milk -= 75
                await pconn.execute("UPDATE events_new SET milk = $1 WHERE u_id = $2", milk, ctx.author.id)
                await ctx.bot.commondb.add_bag_item(
                    ctx.author.id,
                    'radiant_gem',
                    amount,
                    True
                )
                await ctx.send(f"You bought {amount}x gleam gems.")
                self.start_purchaselock.remove(ctx.author.id)
                return

            if option == 3:
                if milk < 50:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                milk -= 50
                inventory = await pconn.fetchrow("SELECT u_id, battle_multiplier FROM users WHERE u_id = $1", ctx.author.id)
                inventory = dict(inventory)

                if inventory['battle_multiplier'] >= 50:
                    await ctx.send("You're maxed out.")
                    self.start_purchaselock.remove(ctx.author.id)
                    return

                new_amount = min(inventory.get("battle_multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE events_new SET milk = $1 WHERE u_id = $2", milk, ctx.author.id)
                await pconn.execute("UPDATE account_bound SET battle_multiplier = $1 WHERE u_id = $2", new_amount, ctx.author.id)
                await ctx.send(f"You bought 2x Battle Multipliers.")
                self.start_purchaselock.remove(ctx.author.id)
                return
            
            if option == 4:
                if milk < 50:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                milk -= 50
                inventory = await pconn.fetchrow("SELECT u_id, shiny_multiplier FROM account_bound WHERE u_id = $1", ctx.author.id)
                inventory = dict(inventory)

                if inventory['shiny_multiplier'] >= 50:
                    await ctx.send("You're maxed out.")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                
                new_amount = min(inventory.get("shiny_multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE events_new SET milk = $1 WHERE u_id = $2", milk, ctx.author.id)
                await pconn.execute("UPDATE account_bound SET shiny_multiplier = $1 WHERE u_id = $2", new_amount, ctx.author.id)
                await ctx.send(f"You bought 2x Shiny Multipliers.")
                self.start_purchaselock.remove(ctx.author.id)
                return
            
            if option == 5:
                if milk < 100:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                milk -= 100
                await pconn.execute("UPDATE users SET raffle = raffle + 1 WHERE u_id = $1", ctx.author.id)
                await pconn.execute("UPDATE events_new SET milk = $1 WHERE u_id = $2", milk, ctx.author.id)
                await ctx.send(f"You were given an entry into the Summer Raffle!\nThe raffle will be drawn in the Mewbot Official Server. `\invite`")       
                self.start_purchaselock.remove(ctx.author.id)
                return
            
            if option == 6:
                if milk < 100:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.start_purchaselock.remove(ctx.author.id)
                    return
                milk -= 100
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "summer2023" not in skins[pokemon]:
                    skins[pokemon]["summer2023"] = 1
                else:
                    skins[pokemon]["summer2023"] += 1
                await pconn.execute("UPDATE events_new SET milk = $1 WHERE u_id = $2", milk, ctx.author.id)
                await pconn.execute("UPDATE users SET skins = $1::json WHERE u_id = $2", skins, ctx.author.id)
                await ctx.send(f"You got a {pokemon} summer skin! Apply it with `/skin apply`.")
                self.start_purchaselock.remove(ctx.author.id)
                return


    #@commands.hybrid_group()
    async def valentine(self, ctx):
        """Valentine Commands."""
        pass

    #@valentine.command(name="buddy")
    async def buddy(self, ctx, member: discord.Member):
        """Choose a buddy for event"""
        #User can't participate in event
        if ctx.author.id == 1075429458271547523:
            return
        if ctx.author.id == member.id:
            await ctx.send("You can't be buddies with yourself, sorry.")
            return
        
        cview = ConfirmView(
            ctx,
            f"{ctx.author.mention} has requested for you to be their buddy!\n*Waiting for {member.mention} to confirm...*",
            allowed_interactors=[member.id],
        )
        if not await cview.wait():
            await cview.message.edit(content="Buddy request denied!")
            return
    
        async with ctx.bot.db[0].acquire() as pconn:
            check = await pconn.fetchval(
                "SELECT valentine FROM users WHERE u_id = $1",
                ctx.author.id
            )
            if check != 0:
                await ctx.send("You've already selected your Valentine Buddy!")
                return
            await pconn.execute(
                "UPDATE users SET valentine = $1 WHERE u_id = $2",
                member.id,
                ctx.author.id
            )
        await ctx.send("You've successfully selected your Valentine's Buddy!")

    #@valentine.command(name="shop")
    async def valentine_shop(self, ctx):
        """Check the valentine shop."""
        if not self.VALENTINE_COMMANDS:
            await ctx.send("This command can only be used during the valentine season!")
            return
        #User can't participate in event
        if ctx.author.id == 1075429458271547523:
            return
        async with self.bot.db[0].acquire() as pconn:
            heart_amount = await pconn.fetchval(
                "SELECT hearts FROM users WHERE u_id = $1",
                ctx.author.id
            )
        embed = discord.Embed(
            title="Valentine Shop",
            description=f"Use <:poke_heart:1075152203297341482> Hearts gained from Raids to purchase items.\nYou have {heart_amount} <:poke_heart:1075152203297341482> Hearts",
            color=random.choice(RED_GREEN),
        )
        embed.add_field(
            name="Currency",
            value="`1.` 3 Redeems\n30 <:poke_heart:1075152203297341482>\n`2.` 1-25 Gleam Gems\n75 <:poke_heart:1075152203297341482>",
            inline=True
        )
        embed.add_field(
            name="Multipliers",
            value="`3.` 2x Battle Multi\n50 <:poke_heart:1075152203297341482>\n`4.` 2x Shiny Multi\n50 <:poke_heart:1075152203297341482>",
            inline=True
        )
        embed.add_field(
            name="Misc",
            value="`5.` 1 Raffle Entry\n100 <:poke_heart:1075152203297341482>\n`6.` Random Valentine Skin\n100 <:poke_heart:1075152203297341482>",
            inline=True
        )
        embed.set_footer(
            text="Use /valentine buy with an option number to buy that item!")
        await ctx.send(embed=embed)

    #@valentine.command(name="buy")
    async def valentine_buy(self, ctx, option: int):
        """Buy something from the valentine shop."""
        if not self.VALENTINE_COMMANDS:
            await ctx.send("This command can only be used during the valentine season!")
            return
        #User can't participate in event
        if ctx.author.id == 1075429458271547523:
            return
        if option < 1 or option > 6:
            await ctx.send("That isn't a valid option. Select a valid option from `/valentine shop`.")
            return
        async with self.bot.db[0].acquire() as pconn:
            holidayinv = await pconn.fetchval("SELECT hearts FROM users WHERE u_id = $1", ctx.author.id)
            if holidayinv == 0:
                await ctx.send("You haven't gotten any hearts yet!")
                return
            if option == 1:
                if holidayinv < 30:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 30
                await pconn.execute("UPDATE users SET redeems = redeems + 3, hearts = $1 WHERE u_id = $2", holidayinv, ctx.author.id)
                await ctx.send("You bought 3 Redeems.")
            if option == 2:
                amount = random.randint(1, 25)
                if holidayinv < 75:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 75
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + amount
                await pconn.execute("UPDATE users SET inventory = $1::json,  hearts = $2 WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought {amount}x gleam gem.")
            if option == 3:
                if holidayinv < 50:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 50
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["battle-multiplier"] = min(
                    inventory.get("battle-multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE users SET inventory = $1::json, hearts = $2 WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 2x Battle Multipliers.")
            if option == 4:
                if holidayinv < 50:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 50
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["shiny-multiplier"] = min(
                    inventory.get("shiny-multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE users SET inventory = $1::json, hearts = $2 WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 2x Shiny Multipliers.")
            if option == 5:
                if holidayinv < 100:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 100
                await pconn.execute("UPDATE users SET raffle = raffle + 1, hearts = $1 WHERE u_id = $2", holidayinv, ctx.author.id)
                await ctx.send(f"You were given an entry into the Valentine Raffle!\nThe raffle will be drawn in the Mewbot Official Server. `\invite`")       
            if option == 6:
                if holidayinv < 100:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 100
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "valentines2023" not in skins[pokemon]:
                    skins[pokemon]["valentines2023"] = 1
                else:
                    skins[pokemon]["valentines2023"] += 1
                await pconn.execute("UPDATE users SET skins = $1::json, hearts = $2 WHERE u_id = $3", skins, holidayinv, ctx.author.id)
                await ctx.send(f"You got a {pokemon} valentine skin! Apply it with `/skin apply`.")

    #@commands.hybrid_group()
    async def halloween(self, ctx):
        """Halloween commands."""
        pass

    #@halloween.command(name="buy")
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

    #@halloween.command(name="inventory")
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

    #@halloween.command(name="shop")
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

    #@halloween.command(name="open_spooky")
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

    #@halloween.command(name="open_fleshy")
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
                weights=(0.35, 0.10, 0.05, 0.15, 0.35),
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

    #@halloween.command(name="open_horrific")
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
            elif reward == "legendchest":
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

    #@commands.hybrid_group()
    async def christmas(self, ctx):
        """Christmas commands."""
        pass

    #@christmas.command(name="spread_cheer")
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

    #@christmas.command(name="buy")
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
            if "snowflakes" not in holidayinv:
                await ctx.send("You haven't gotten any snowflakes yet!")
                return
            if option == 1:
                if holidayinv["snowflakes"] < 25:
                    await ctx.send("You don't have enough snowflakes for that!")
                    return
                holidayinv["snowflakes"] -= 25
                await pconn.execute("UPDATE users SET redeems = redeems + 5, holidayinv = $1::json WHERE u_id = $2", holidayinv, ctx.author.id)
                await ctx.send("You bought 5 Redeems.")
            if option == 2:
                if holidayinv["snowflakes"] < 50:
                    await ctx.send("You don't have enough snowflakes for that!")
                    return
                holidayinv["snowflakes"] -= 50
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["battle-multiplier"] = min(
                    inventory.get("battle-multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE users SET inventory = $1::json, holidayinv = $2::json WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 2x Battle Multipliers.")
            if option == 3:
                if holidayinv["snowflakes"] < 50:
                    await ctx.send("You don't have enough snowflakes for that!")
                    return
                holidayinv["snowflakes"] -= 50
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["shiny-multiplier"] = min(
                    inventory.get("shiny-multiplier", 0) + 2, 50)
                await pconn.execute("UPDATE users SET inventory = $1::json, holidayinv = $2::json WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 2x Shiny Multipliers.")
            if option == 4:
                amount = random.randint(1, 25)
                if holidayinv["snowflakes"] < 75:
                    await ctx.send("You don't have enough snowflakes for that!")
                    return
                holidayinv["snowflakes"] -= 75
                inventory = await pconn.fetchval("SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + amount
                await pconn.execute("UPDATE users SET inventory = $1::json, holidayinv = $2::json WHERE u_id = $3", inventory, holidayinv, ctx.author.id)
                await ctx.send(f"You bought 1x gleam gem.")
            if option == 5:
                if holidayinv["snowflakes"] < 100:
                    await ctx.send("You don't have enough snowflakes for that!")
                    return
                holidayinv["snowflakes"] -= 100
                await pconn.execute("UPDATE users SET raffle = raffle + 1 WHERE u_id = $1", ctx.author.id)
                await ctx.send(f"You were given an entry into the Christmas Raffle!\nThe raffle will be drawn in the Mewbot Official Server. `\invite`")
            if option == 6:
                if holidayinv["snowflakes"] < 150:
                    await ctx.send("You don't have enough snowflakes for that!")
                    return
                holidayinv["snowflakes"] -= 150
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

    #@christmas.command(name="inventory")
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
            description=f"Use `/christmas shop` to see what snowflakes can be used for!",
            color=random.choice(RED_GREEN),
        )
        if "snowflakes" in inventory:
            embed.add_field(name="Snowflakes", value=f"{inventory['snowflakes']}x")
        if "small gift" in inventory:
            embed.add_field(name="Small Present",
                            value=f"{inventory['small gift']}x")
        if "large gift" in inventory:
            embed.add_field(name="Large Present",
                            value=f"{inventory['large gift']}x")
        #if "holiday cheer" in inventory:
            #embed.add_field(name="Holiday Cheer",
                            #value=f"{inventory['holiday cheer']}x")
        embed.set_footer(
            text="Happy Holidays!")
        await ctx.send(embed=embed)

    #@christmas.command(name="shop")
    async def christmas_shop(self, ctx):
        """Check the christmas shop."""
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        desc = (
            "**Option# | Price | Item**\n"
            "**1** | 25 <:snowflake:1055702885041721374> | 5 Redeems\n"
            "**2** | 50 <:snowflake:1055702885041721374> | 2x Battle Multi\n"
            "**3** | 50 <:snowflake:1055702885041721374> | 2x Shiny Multi\n"
            "**4** | 75 <:snowflake:1055702885041721374> | 1-25 Gleam Gems\n"
            "**5** | 100 <:snowflake:1055702885041721374> | 1x Raffle Entry\n"
            "**6** | 150 <:snowflake:1055702885041721374> | Random Christmas Skin\n"
        )
        embed = discord.Embed(
            title="Christmas Shop",
            description="Use leftover <:snowflake:1055702885041721374> Snowflakes to purchase items",
            color=random.choice(RED_GREEN),
        )
        embed.add_field(
            name="Currency",
            value="5 Redeems\n25 <:snowflake:1055702885041721374>\n1-25 Gleam Gems\n75 <:snowflake:1055702885041721374>",
            inline=True
        )
        embed.add_field(
            name="Multipliers",
            value="2x Battle Multi\n50 <:snowflake:1055702885041721374>\n2x Shiny Multi\n50 <:snowflake:1055702885041721374>",
            inline=True
        )
        embed.add_field(
            name="Misc",
            value="1 Raffle Entry\n100 <:snowflake:1055702885041721374>\nRandom Christmas Skin\n150 <:snowflake:1055702885041721374>",
            inline=True
        )
        embed.set_footer(
            text="Use /christmas buy with an option number to buy that item!")
        await ctx.send(embed=embed)

    #@christmas.command(name="open_smallgift")
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
            ("skin", "snowflakes", "redeem", "energy", "shinyice"),
            weights=(.10, 0.30, 0.15, 0.30, 0.15),
        )[0]
        if reward == "skin":
            async with ctx.bot.db[0].acquire() as pconn:
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "xmas2022" not in skins[pokemon]:
                    skins[pokemon]["xmas2022"] = 1
                else:
                    skins[pokemon]["xmas2022"] += 1
                await pconn.execute("UPDATE users SET skins = $1::json WHERE u_id = $2", skins, ctx.author.id)
            msg = (
                f"You opened the gift, and inside was a christmas skin for your {pokemon} to wear!\n"
                "Use `/skin apply` to apply it to a pokemon.\n"
            )
        elif reward == "snowflakes":
            async with ctx.bot.db[0].acquire() as pconn:
                snowflakes = random.randint(1, 10)
                inventory = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
                inventory["snowflakes"] = inventory.get("snowflakes", 0) + snowflakes
                await pconn.execute("UPDATE users SET holidayinv = $1::json WHERE u_id = $2", inventory, ctx.author.id)
            msg = f"You opened the gift, and inside was {snowflakes} Snowflakes!\n"
        elif reward == "redeem":
            amount = random.randint(1, 5)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} Redeems!\n"
        elif reward == "energy":
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute("UPDATE users SET energy = energy + 2 WHERE u_id = $1", ctx.author.id)
            msg = "You stole some of Santa's cookies and milk! It restored some energy!\n"
        elif reward == "shinyice":
            pokemon = random.choice(await self.get_ice())
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True)
            msg = f"You received a Shiny {pokemon}!\n"
        await ctx.send(msg)

    #@christmas.command(name="open_largegift")
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
            ("skin", "redeem", "chest", "boostedice", "shinyice"),
            weights=(.20, 0.35, 0.15, 0.20, 0.10),
        )[0]
        if reward == "skin":
            async with ctx.bot.db[0].acquire() as pconn:
                skins = await pconn.fetchval("SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id)
                pokemon = random.choice(
                    list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "xmas2022" not in skins[pokemon]:
                    skins[pokemon]["xmas2022"] = 1
                else:
                    skins[pokemon]["xmas2022"] += 1
                await pconn.execute("UPDATE users SET skins = $1::json WHERE u_id = $2", skins, ctx.author.id)
            msg = (
                f"You opened the gift, and inside was a christmas skin for your {pokemon} to wear!\n"
                "Use `/skin apply` to apply it to a pokemon.\n"
            )
        elif reward == "redeem":
            amount = random.randint(5, 10)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} Redeems!\n"
        elif reward == 'chest':
            chest = random.choices(
                ("rare", "mythic", "legend"),
                weights=(.60, .20, .10),
            )[0]
            async with ctx.bot.db[0].acquire() as pconn:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                if chest == 'rare':
                    inventory["rare chest"] = inventory.get("rare chest", 0) + 1
                    msg = "You received a Rare Chest!\n"
                elif chest == 'mythic':
                    inventory["mythic chest"] = inventory.get("mythic chest", 0) + 1
                    msg = "You received a Mythic Chest!\n"
                elif chest == 'legend':
                    inventory["legend chest"] = inventory.get("legend chest", 0) + 1
                    msg = "You received a Legend Chest!\n"
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    ctx.author.id,
                )
        elif reward == "boostedice":
            pokemon = random.choice(await self.get_ice())
            pokedata = await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, boosted=True)
            msg = f"You received a Boosted IV {pokedata.emoji}{pokemon}!\n"
        elif reward == "shinyice":
            pokemon = random.choice(await self.get_ice())
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, shiny=True)
            msg = f"You received a shiny {pokemon}!\n"
        #Large Gift gives Snowflakes
        snowflakes = random.randint(1, 5)
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchval("SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id)
            inventory["snowflakes"] = inventory.get("snowflakes", 0) + snowflakes
            await pconn.execute("UPDATE users SET holidayinv = $1::json WHERE u_id = $2", inventory, ctx.author.id)
        msg += f"There was also {snowflakes} Snowflakes!\n"
        await ctx.send(msg)

    #@christmas.command(name="gift")
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

    #@commands.hybrid_group()
    async def unown(self, ctx):
        """Unown commands"""
        pass

    #@unown.command(name="guess")
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

    #@unown.command(name="inventory")
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

    #@unown.command(name="start")
    #@check_mod()
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
        """Gives some carrots to the provided user."""
        carrots = random.randint(5, 10)
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute("INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING", user.id)
            await pconn.execute(f"UPDATE events_new SET carrots = carrots + $1 WHERE u_id = $2", carrots, user.id)
            embed = discord.Embed(
                title="Easter Event!",
                description=f"The Pokemon was holding {carrots}x 🥕s!\nUse command `/easter shop` to use them!",
                color=ORANGE,
            )
        await channel.send(embed=embed)

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
        # async with self.bot.db[0].acquire() as pconn:
        # honey = await pconn.fetchval(
        #"SELECT type FROM honey WHERE channel = $1 LIMIT 1",
        # channel.id,
        # )
        # if honey != "cheer":
        # return
        await asyncio.sleep(random.randint(30, 60))
        await ChristmasSpawn(
            self, channel, random.choice(self.EVENT_POKEMON)
        ).start()

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
        return
        if self.bot.botbanned(user.id) or channel.guild.id != 998128574898896906:
            return
        if self.EASTER_DROPS:
            if not random.randrange(10):
                await self.give_egg(channel, user)
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
        if self.HALLOWEEN_DROPS:
            if not random.randrange(30):
                await self.give_candy(channel, user)
            if not random.randrange(10):
                await self.maybe_spawn_christmas(channel)
        if self.CHRISTMAS_DROPS:
            #if not random.randrange(15) or user.id == 334155028170407949:
                #await self.give_cheer(channel, user)
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
        if self.VALENTINE_DROPS:
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
        if self.SUMMER_DROPS:
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)

        #if not random.randrange(10):
            #await self.maybe_spawn_unown(channel)

    @commands.Cog.listener()
    async def on_poke_fish(self, channel, user):
        return
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
        return
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS:
            if not random.randrange(10):
                await self.give_egg(channel, user)
        if self.HALLOWEEN_DROPS:
            if not random.randrange(200):
                await self.give_scary_mask(channel, user)
            elif not random.randrange(25):
                await self.give_bone(channel, user)
            elif not random.randrange(4):
                await self.give_candy(channel, user)
        #if not random.randrange(7):
            #await self.maybe_spawn_unown(channel)


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
        self.banned = [
            1075429458271547523,
        ]

    async def interaction_check(self, interaction):
        if self.state == "registering":
            if interaction.user in self.registered:
                await interaction.response.send_message(
                    content="You have already joined!", ephemeral=True
                )
                return False
            return True
        elif self.state == "attacking":
            if interaction.user in self.attacked:
                await interaction.response.send_message(
                    content="You have already attacked!", ephemeral=True
                )
                return False
            if interaction.user not in self.registered:
                await interaction.response.send_message(
                    content="You didn't join the battle! You can't attack this one.",
                    ephemeral=True,
                )
                return False
            return True
        else:
            await interaction.response.send_message(
                content="This battle has already ended!", ephemeral=True
            )
            return False

    async def start(self):
        extra_msg = ""
        pokeurl = (
            "http://dyleee.github.io/mewbot-images/sprites/" 
            + await get_file_name(self.poke, self.cog.bot, skin="summer2023")
        )
        guild = await self.cog.bot.mongo_find("guilds", {"id": self.channel.guild.id})
        if guild is None:
            small_images = False
        else:
            small_images = guild["small_images"]
        self.embed = discord.Embed(
            title="A Summer Pokémon Appears!",
            description="Join the battle to take it down.",
            color=0x0084FD,
        )
        self.embed.add_field(name="Take Action", value="Click the Button to join!")
        if small_images:
            self.embed.set_thumbnail(url=pokeurl)
        else:
            self.embed.set_image(url=pokeurl)
        self.add_item(RaidJoin())
        
        #Checks if message is in Official to use Raid Ping
        if self.channel.guild.id == 998128574898896906:
            am = discord.AllowedMentions.none()
            am.roles = True
            ping = '<@&998320324477190184>'
            self.message = await self.channel.send(ping, embed=self.embed, view=self, allowed_mentions=am)
        else:
            self.message = await self.channel.send(embed=self.embed, view=self)
            
        await asyncio.sleep(20)
        self.clear_items()

        if not self.registered:
            embed = discord.Embed(
                title="The Summer Pokémon ran away!",
                color=0x0084FD,
            )
            if small_images:
                embed.set_thumbnail(url=pokeurl)
            else:
                embed.set_image(url=pokeurl)
            await self.message.edit(embed=embed, view=None)
            return
        
        #Old system that uses CHRISTAS MOVES above
        #moves = []
        #for idx, move in enumerate(self.cog.CHRISTMAS_MOVES[self.poke]):
            #damage = max(2 - idx, 0)
            #moves.append(RaidMove(move, damage))
        #random.shuffle(moves)
        #for move in moves:
            #self.add_item(move)
        
        #New move system from skins
        # Calculate valid moves of each effectiveness tier
        form_info = await self.cog.bot.db[1].forms.find_one(
            {"identifier": self.poke.lower()}
        )
        type_ids = (
            await self.cog.bot.db[1].ptypes.find_one({"id": form_info["pokemon_id"]})
        )["types"]
        type_effectiveness = {}
        for te in await self.cog.bot.db[1].type_effectiveness.find({}).to_list(None):
            type_effectiveness[(te["damage_type_id"], te["target_type_id"])] = te[
                "damage_factor"
            ]
        super_types = []
        normal_types = []
        un_types = []
        for attacker_type in range(1, 19):
            effectiveness = 1
            for defender_type in type_ids:
                effectiveness *= (
                    type_effectiveness[(attacker_type, defender_type)] / 100
                )
            if effectiveness > 1:
                super_types.append(attacker_type)
            elif effectiveness < 1:
                un_types.append(attacker_type)
            else:
                normal_types.append(attacker_type)
        super_raw = (
            await self.cog.bot.db[1]
            .moves.find(
                {"type_id": {"$in": super_types}, "damage_class_id": {"$ne": 1}}
            )
            .to_list(None)
        )
        super_moves = [
            x["identifier"].capitalize().replace("-", " ") for x in super_raw
        ]
        normal_raw = (
            await self.cog.bot.db[1]
            .moves.find(
                {"type_id": {"$in": normal_types}, "damage_class_id": {"$ne": 1}}
            )
            .to_list(None)
        )
        normal_moves = [
            x["identifier"].capitalize().replace("-", " ") for x in normal_raw
        ]
        un_raw = (
            await self.cog.bot.db[1]
            .moves.find({"type_id": {"$in": un_types}, "damage_class_id": {"$ne": 1}})
            .to_list(None)
        )
        un_moves = [x["identifier"].capitalize().replace("-", " ") for x in un_raw]

        # Add the moves to the view
        moves = []
        for i in range(4):
            if i == 0:
                move_name = random.choice(super_moves)
                type_id = await self.cog.bot.db[1].moves.find_one({"identifier": move_name.replace(" ", "-").lower()})
                type_emoji = self.cog.bot.misc.get_type_emote((await self.cog.bot.db[1].types.find_one({"id": type_id['type_id']}))["identifier"])
                moves.append(RaidMove(move_name, 2, type_emoji))
            if i == 1:
                move_name = random.choice(normal_moves)
                type_id = await self.cog.bot.db[1].moves.find_one({"identifier": move_name.replace(" ", "-").lower()})
                type_emoji = self.cog.bot.misc.get_type_emote((await self.cog.bot.db[1].types.find_one({"id": type_id['type_id']}))["identifier"])
                moves.append(RaidMove(move_name, 1, type_emoji))
            elif i == 2:
                move_name = random.choice(un_moves)
                type_id = await self.cog.bot.db[1].moves.find_one({"identifier": move_name.replace(" ", "-").lower()})
                type_emoji = self.cog.bot.misc.get_type_emote((await self.cog.bot.db[1].types.find_one({"id": type_id['type_id']}))["identifier"])
                moves.append(RaidMove(move_name, 0, type_emoji))
            elif i == 3:
                move_name = random.choice(un_moves)
                type_id = await self.cog.bot.db[1].moves.find_one({"identifier": move_name.replace(" ", "-").lower()})
                type_emoji = self.cog.bot.misc.get_type_emote((await self.cog.bot.db[1].types.find_one({"id": type_id['type_id']}))["identifier"])
                moves.append(RaidMove(move_name, 0, type_emoji))
            else:
                pass
            
        random.shuffle(moves)
        for move in moves:
            self.add_item(move)

        self.max_hp = int(len(self.registered) * 1.25)
        self.embed = discord.Embed(
            title="A Summer Pokémon has spawned, attack it with everything you've got!",
            color=0x0084FD,
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
                title="The Summer Pokémon got away!",
                color=0x0084FD,
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
            for attacker, damage in self.attacked.items():
                if damage == 2:
                    carrot_min = 20
                    carrot_max = 30
                elif damage == 1:
                    carrot_max = 15
                    carrot_min = 10
                elif damage == 0:
                    carrot_max = 5
                    carrot_min = 1
                carrots_gained = random.randint(carrot_min, carrot_max)
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING", 
                    attacker.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET milk = milk + $1 WHERE u_id = $2", 
                    carrots_gained, 
                    attacker.id
                )

        self.embed = discord.Embed(
            title=f"The Summer Pokémon was defeated! Attackers have been awarded. {extra_msg}",
            color=0x0084FD,
        )
        if small_images:
            self.embed.set_thumbnail(url=pokeurl)
        else:
            self.embed.set_image(url=pokeurl)
        await self.message.edit(embed=self.embed, view=None)

class RaidJoin(discord.ui.Button):
    """A button to join an pokemon raid."""

    def __init__(self):
        super().__init__(label="Join", style=discord.ButtonStyle.green)

    async def callback(self, interaction):
        self.view.registered.append(interaction.user)
        await interaction.response.send_message(
            content="You have joined the battle!", ephemeral=True
        )


class RaidMove(discord.ui.Button):
    """A move button for attacking a christmas pokemon."""
    def __init__(self, move, damage, emote):
        super().__init__(
            label=move,
            emoji=emote,
            style=discord.ButtonStyle.gray
        )
        self.move = move
        self.damage = damage
        self.emote = emote

        if damage == 2:
            #self.effective = "It's super effective! You will get a Large Present if the poke is defeated."
            #self.effective = "It's super effective! You'll receive hearts if the poke is defeated!"
            self.effective = "It's Super Effective! You will get a 20-30 🥛 if the Pokemon is defeated."
        elif damage == 1:
            #self.effective = "It's not very effective... You will get a Small Present if the poke is defeated."
            #self.effective = "It's not very effective... You'll receive hearts if the poke is defeated!"
            self.effective = "It's not Very Effective... You will get a 10-15 🥛 if the Pokemon is defeated."
        else:
            #self.effective = "It had no effect... You will only get Snowflakes if the poke is defeated."
            #self.effective = "It had no effect... You'll receive hearts if the poke is defeated!"
            self.effective = "It had No Effect... You will get a 1-5 🥛 if the Pokemon is defeated."

    async def callback(self, interaction):
        self.view.attacked[interaction.user] = self.damage
        await interaction.response.send_message(content=f"You used {self.move}. {self.effective}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Events(bot))