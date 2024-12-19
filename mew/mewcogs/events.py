from io import BytesIO
import json
import os
import discord
import random
import asyncio
import time

from unicodedata import name
from discord.ext import commands
from mewcogs.json_files import make_embed
from mewcogs.pokemon_list import *
from mewutils.checks import tradelock, check_mod
from mewutils.misc import get_file_name, get_emoji, ConfirmView, MenuView, pagify
from collections import defaultdict
from datetime import datetime
from typing import Coroutine, Literal
from dataclasses import dataclass

ORANGE = 0xF4831B
RED_GREEN = [0xBB2528, 0x146B3A]
XMAS_ROLE = 1184182751067377674

GLEAM_POKEMON = [
    "Cutiefly",
    "Flabebe",
    "Darkrai",
    "Larvitar",
    "Scraggy",
    "Nihilego",
    "Cleffa",
    "Zeraora",
    "Cresselia",
    "Shaymin",
    "Dratini",
    "Wooper",
    "Wurmple",
    "Lunatone",
    "Reshiram",
    "Meltan",
    "Zapdos-galar",
    "Charmander",
    "Deerling",
    "Unown",
    "Pancham",
    "Corphish",
    "Kyogre",
    "Cyndaquil",
    "Ralts",
    "Magikarp",
    "Heracross",
    "Drowzee",
    "Porygon",
    "Shellder",
    "Chingling",
    "Entei",
    "Zapdos",
    "Weedle",
    "Mawile",
    "Omanyte",
    "Anorith",
    "Togepi",
    "Torkoal",
    "Bellsprout",
    "Piplup",
    "Treecko",
    "Axew",
    "Clamperl",
    "Scyther",
    "Latios",
    "Deoxys",
    "Poliwag",
    "Roggenrola",
    "Yveltal",
    "Liligant",
    "Landorus",
    "Aegislash",
    "Infernape",
    "Gastrodon",
    "Chesnaught",
    "Zoroark",
    "Arceus",
    "Pheromosa",
    "Rotom",
    "Goomy",
    "Milcery",
    "Minccino",
    "Turtwig",
    "Salandit",
    "Scorbunny",
    "Dreepy",
    "Tornadus",
    "Genesect",
    "Groudon",
    "Xurkitree",
    "Popplio",
    "Litten",
    "Chikorita",
    "Noibat",
    "Sneasel",
    "Impidimp",
    "Eternatus",
    "Mudkip",
    "Zacian",
    "Giratina",
    "Dracovish",
    "Budew ",
    "Spritzee ",
    "Koraidon ",
    "Vulpix-alola ",
    "Teddiursa",
    "Skarmory",
    "Solosis",
    "Hawlucha",
    "Sentret",
    "Diancie",
    "Audino",
    "Tapu-fini",
    "Suicune",
    "Froakie",
]

RADIANT_POKEMON = [
    "Necrozma",
    "Yveltal",
    "Salamence",
    "Xerneas",
    "Eevee",
    "Charmander",
    "Celebi",
    "Riolu",
    "Rockruff",
    "Zorua",
    "Dreepy",
    "Lapras",
    "Tyrantrum",
    "Mimikyu",
    "Jynx",
]

uncoded_ids = [
    266,
    270,
    476,
    495,
    502,
    511,
    597,
    602,
    603,
    607,
    622,
    623,
    624,
    625,
    626,
    627,
    628,
    629,
    630,
    631,
    632,
    633,
    634,
    635,
    636,
    637,
    638,
    639,
    640,
    641,
    642,
    643,
    644,
    645,
    646,
    647,
    648,
    649,
    650,
    651,
    652,
    653,
    654,
    655,
    656,
    657,
    658,
    671,
    695,
    696,
    697,
    698,
    699,
    700,
    701,
    702,
    703,
    719,
    723,
    724,
    725,
    726,
    727,
    728,
    811,
    10001,
    10002,
    10003,
    10004,
    10005,
    10006,
    10007,
    10008,
    10009,
    10010,
    10011,
    10012,
    10013,
    10014,
    10015,
    10016,
    10017,
    10018,
]


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


class ListSelectChristmas(discord.ui.Select):
    """Drop down selection for trainer image"""

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Swimmerm", emoji="<:swimmerm:1273436007794212874>"
            ),
            discord.SelectOption(
                label="Swimmerf", emoji="<:swimmerf:1273436006678401105>"
            ),
            discord.SelectOption(
                label="Cyclist", emoji="<:cyclist:1273436027649921096>"
            ),
            discord.SelectOption(label="Dancer", emoji="<:dancer:1273436026680905812>"),
        ]
        super().__init__(options=options)

    async def callback(self, interaction):
        self.view.choice = interaction.data["values"][0]
        self.view.event.set()


class ListSelectView(discord.ui.View):
    """View to handle trainer selection"""

    def __init__(self, ctx, confirm_content: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.choice = None
        self.event = asyncio.Event()
        self.confirm_content = confirm_content
        self.add_item(ListSelectChristmas())

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content="You are not allowed to interact with this button.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        try:
            await self.message.edit(view=None)
        except discord.NotFound:
            pass
        self.event.set()

    async def on_error(self, interaction, error, item):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def wait(self):
        """Returns the user's choice, or None if they did not choose in time."""
        self.message = await self.ctx.send(self.confirm_content, view=self)
        await self.event.wait()
        return self.choice


# Here for Easter 2023 Event
async def get_egg(ctx, fund):
    shiny = False
    boosted = False
    # Proceed to generate egg and add to user
    max_chance = 28000 - fund
    special_chance = random.randint(1, max_chance)

    # 5. Boosted Legendary, 5% Shiny
    if special_chance <= 2500:  # 10%
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (ubList, LegendList),
            weights=(0.7, 0.3),
        )[0]
        poke_name = random.choice(choiceList)

    # 4. Boosted 80% UB/ 20% Legendary, 10% Shiny
    elif special_chance <= 5000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pseudoList, ubList, LegendList),
            weights=(0.4, 0.4, 0.2),
        )[0]
        poke_name = random.choice(choiceList)

    # 3. 40% Boosted Psu, 25% Shiny
    elif special_chance <= 10000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pseudoList, ubList),
            weights=(0.9, 0.1),
        )[0]
        poke_name = random.choice(choiceList)

    # 2. 60% Boosted Starter/Pokemon, 75% Shiny
    elif special_chance <= 15000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pList, starterList, pseudoList),
            weights=(0.5, 0.4, 0.1),
        )[0]
        poke_name = random.choice(choiceList)

    # 1. Boosted Starter or Pseudo, 80% Shiny
    elif special_chance <= 24000:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        choiceList = random.choices(
            (pList, starterList),
            weights=(0.8, 0.2),
        )[0]
        poke_name = random.choice(choiceList)

    # Boosted Normal Pokemon, 80% Shiny (Edge Case)
    else:
        if (random.randint(1, 100)) <= 10:
            shiny = True
        if (random.randint(1, 100)) <= 10:
            boosted = True
        poke_name = random.choice(pList)

    # Generate Egg Stats
    # IVs and Nature
    min_iv = 13 if boosted else 1
    max_iv = 31 if boosted or random.randint(0, 1) else 29
    hpiv = random.randint(min_iv, max_iv)
    atkiv = random.randint(min_iv, max_iv)
    defiv = random.randint(min_iv, max_iv)
    spaiv = random.randint(min_iv, max_iv)
    spdiv = random.randint(min_iv, max_iv)
    speiv = random.randint(min_iv, max_iv)
    nature = random.choice(natlist)

    # Everything else
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

    # Gender
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


# Here for Easter 2023 Event
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
        skin,
    )
    return query2, args


class Events(commands.Cog):
    """Various seasonal events in Mewbot."""

    def __init__(self, bot):
        self.bot = bot
        # Seasonal toggles
        self.EASTER_DROPS = False
        self.EASTER_COMMANDS = False
        self.HALLOWEEN_DROPS = False
        self.HALLOWEEN_COMMANDS = False
        self.CHRISTMAS_DROPS = False
        self.CHRISTMAS_COMMANDS = False
        self.VALENTINE_DROPS = False
        self.VALENTINE_COMMANDS = False
        self.SUMMER_DROPS = False
        self.SUMMER_COMMANDS = False
        self.HALLOWEEN_RADIANT = [
            "Plusle",
            "Minun",
            "Mimikyu",
            "Keldeo",
            "Cacnea",
            "Makuhita",
            "Yamask",
            "Solosis",
            "Spiritomb",
            "Illumise",
            "Pincurchin",
            "Golett",
            "Dialga",
        ]
        # "Poke name": ["Super effective (2)", "Not very (1)", "No effect (0)", "No effect (0)"]
        self.CHRISTMAS_MOVES = {
            "Arceus": ["Close Combat", "Tackle", "Shadow Claw", "Shadow Sneak"],
            "Charizard": ["Rock slide", "Solar Beam", "Will O Wisp", "Howl"],
            "Caterpie": ["Flame Burst", "Sand Tomb", "Quiver Dance", "Poison Powder"],
            "Diglett": ["Water Shuriken", "Rock Slide", "Growl", "Sleep Powder"],
            "Mew": ["Dark Pulse", "Extrasensory", "Block", "Gravity"],
            "Miltank": ["Close Combat", "Echoed Voice", "Healing Wish", "Sandstorm"],
            "Torchic": ["Dive", "Pyro Ball", "Toxic", "Sunny Day"],
            "Gardevoir": ["Shadow Ball", "Earthquake", "Magic Room", "Recover"],
            "Manaphy": ["Leaf Blade", "Ice Beam", "Helping Hand", "Reflect"],
            "Victini": ["Dark Pulse", "Psychic", "Will O Wisp", "Toxic"],
            "Dedenne": ["Earthquake", "Close Combat", "Outrage,", "Dragon Tail"],
            "Carbink": ["Metal Claw", "Psychic", "Dragon Claw", "Scale Shot"],
            "Pheromosa": ["Ember", "Axe Kick", "Mat Block", "Protect"],
            "Lunala": ["Poltergeist", "Moonblast", "Bulk up", "Tackle"],
            "Mimikyu": ["Moongeist Beam", "Belch", "Outrage", "Shadow Sneak"],
            "Scorbunny": ["Snipe Shot", "Grassy Glide", "Court Change", "Taunt"],
            "Raboot": ["Snipe Shot", "Grassy Glide", "Court Change", "Taunt"],
        }
        self.EVENT_POKEMON = [
            "Mew",
            "Ditto",
            "Absol",
            "Snivy",
            "Servine",
            "Serperior",
            "Fennekin",
            "Braixen",
            "Delphox",
            "Lotad",
            "Lombre",
            "Ludicolo",
            "Spinda",
            "Lunatone",
            "Luvdisc",
            "Pidove",
            "Tranquill",
            "Unfezant",
            "Comfey",
            "Buzzwole",
            "Pineco",
            "Forretress",
            "Azurill",
            "Marill",
            "Azumarill",
            "Heracross",
        ]
        self.UNOWN_WORD = None
        self.UNOWN_GUESSES = []
        self.UNOWN_MESSAGE = None
        self.UNOWN_CHARACTERS = [
            {
                "a": "<:emoji_1:980642261375275088>",
                "b": "<:emoji_2:980642329838887002>",
                "c": "<:emoji_3:980643284810604624>",
                "d": "<:emoji_4:980643355136524298>",
                "e": "<:emoji_5:980643389005525042>",
                "f": "<:emoji_6:980643421519749150>",
                "g": "<:emoji_7:980643480005128272>",
                "h": "<:emoji_8:980643523105792050>",
                "i": "<:emoji_9:980643960840142868>",
                "j": "<:emoji_10:980644034978648115>",
                "k": "<:emoji_11:980644080591720471>",
                "l": "<:emoji_12:980644136543735868>",
                "m": "<:emoji_13:980644168244289567>",
                "n": "<:emoji_14:980644255427084328>",
                "o": "<:emoji_15:980644320052916236>",
                "p": "<:emoji_16:980644377506492456>",
                "q": "<:emoji_17:980644413057421332>",
                "r": "<:emoji_18:980644457777086494>",
                "s": "<:emoji_19:980644499971768380>",
                "t": "<:emoji_20:980644531903025212>",
                "u": "<:emoji_21:980644565751054436>",
                "v": "<:emoji_22:980644667928477746>",
                "w": "<:emoji_23:980644751097348146>",
                "x": "<:emoji_24:980644781313097808>",
                "y": "<:emoji_25:980644826947129425>",
                "z": "<:emoji_26:980644947587923989>",
                "!": "<:emoji_27:980645036456828948>",
                "?": "<:emoji_28:980645086067032155>",
            },
            {
                "l": "<:emoji_29:980547575717429308>",
                "d": "<:emoji_30:980547603605381190>",
                "i": "<:emoji_31:980547628607623168>",
                "k": "<:emoji_32:980547656965324861>",
                "e": "<:emoji_33:980547682298900510>",
                "b": "<:emoji_34:980547714922188841>",
                "n": "<:emoji_35:980547739429507073>",
                "j": "<:emoji_36:980547764637282355>",
                "a": "<:emoji_37:980547791006875708>",
                "f": "<:emoji_38:980547820127920138>",
                "m": "<:emoji_39:980547852545691668>",
                "g": "<:emoji_40:980547877581496452>",
                "h": "<:emoji_41:980547904525725776>",
                "c": "<:emoji_42:980547940441534595>",
                "z": "<:emoji_43:980547990219546654>",
                "y": "<:emoji_44:980548022981230632>",
                "?": "<:emoji_45:980548050823032862>",
                "!": "<:emoji_46:980548077427499080>",
                "w": "<:emoji_47:980548114572267570>",
                "q": "<:emoji_48:980548145085821009>",
                "p": "<:emoji_49:980548175360303114>",
                "u": "<:emoji_50:980548210319818792>",
                "x": "<:emoji_43:980548384156946553>",
                "t": "<:emoji_44:980548409784152136>",
                "o": "<:emoji_45:980548441509859409>",
                "s": "<:emoji_46:980548467694895155>",
                "r": "<:emoji_47:980548498132979773>",
                "v": "<:emoji_48:980548529963556946>",
            },
        ]
        self.UNOWN_POINTS = {
            "a": 1,
            "b": 3,
            "c": 3,
            "d": 2,
            "e": 1,
            "f": 4,
            "g": 2,
            "h": 4,
            "i": 1,
            "j": 8,
            "k": 5,
            "l": 1,
            "m": 3,
            "n": 1,
            "o": 1,
            "p": 3,
            "q": 10,
            "r": 1,
            "s": 1,
            "t": 1,
            "u": 1,
            "v": 4,
            "w": 4,
            "x": 8,
            "y": 4,
            "z": 10,
            "!": 1,
            "?": 1,
        }
        self.UNOWN_WORDLIST = []
        self.purchaselock = []
        try:
            with open(self.bot.app_directory / "shared" / "data" / "wordlist.txt") as f:
                self.UNOWN_WORDLIST = f.readlines().copy()
        except Exception:
            pass

    # @commands.hybrid_group()
    async def easter(self, ctx: commands.Context): ...

    # @easter.command(name="info")
    async def easter_info(self, ctx):
        embed = discord.Embed(
            title="Mewbot Easter Event 2023",
            description="More details on the event and how things are working!",
            color=0x00FF00,
        )
        embed.add_field(
            name="Raids",
            value="Raids have a chance of spawning after a Pokemon is caught in your server. Nothing special needs to be done to active them and they drop 🥕",
            inline=True,
        )
        embed.add_field(
            name="Shop and Carrots 🥕",
            value="There is a shop that offers bot wide benefits. Uses 🥕 as currency. They can be earned with Raids or as a drop during Breeding",
            inline=True,
        )
        embed.add_field(
            name="Event Skins",
            value="In the shop for the duration of the event. Can be assigned to any Pokemon the skin belongs too.",
            inline=True,
        )
        embed.add_field(
            name="Winter Fund and Eggs",
            value=(
                "The Easter Bunny has provided us with the opportunity to gain **Painted Eggs**. They are available in the shop for 50 🥕."
                "The Winter Fund is the Easter Bunny's storage for the Winter! By increasing your fund, Diggersby is more likely to give you a Boosted and/or Shiny Egg"
                "These eggs can be **any** Pokemon from the bot! As you donate more the choice of Pokemon your egg can be gets better and better"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    # @easter.command(name="shop")
    async def easter_shop(self, ctx):
        """Check the easter shop."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the Easter Season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            try:
                dets = await pconn.fetchrow(
                    "SELECT carrots, easter_fund FROM events_new WHERE u_id = $1",
                    ctx.author.id,
                )
            except:
                dets = None

            if dets is None:
                carrots = 0
                fund = 0
            else:
                carrots = dets["carrots"]
                fund = dets["easter_fund"]

        embed = discord.Embed(
            title="Easter Shop",
            description=f"Event details can be found with `/easter info`.\nBuy with `/easter buy`\n`Carrots`: {carrots:,} - `Winter Fund`: {fund:,}/25,000",
            color=0x00FF00,
        )
        embed.add_field(
            name="General <a:radiantgem:774866137472827432>",
            value="1-25 Gleam <a:radiantgem:774866137472827432>\n75 🥕\nEaster Skin\n150 🥕",
            inline=True,
        )
        embed.add_field(
            name="Multipliers ",
            value="2x Battle Multi ⏫\n50 🥕\n2x Shiny Multi ⏫\n50 🥕",
            inline=True,
        )
        embed.add_field(
            name="Eggs <:poke_egg:676810968000495633>",
            value="Egg and Redeem\n50 🥕\nEgg and Fund Increase\n150 🥕",
            inline=True,
        )
        embed.set_thumbnail(url="https://mewbot.xyz/diggersby.png")
        embed.set_footer(text="Diggersby Image made by @Ort.Homeless on Instagram!")
        await ctx.send(embed=embed)

    # @easter.command(name="buy")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def easter_buy(
        self,
        ctx,
        option: Literal[
            "Gleam Gems",
            "Easter Skin",
            "Battle Mult.",
            "Shiny Mult.",
            "Fund",
            "Painted Egg",
        ],
    ):
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the Easter Season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            try:
                dets = await pconn.fetchrow(
                    "SELECT carrots, easter_fund FROM events_new WHERE u_id = $1",
                    ctx.author.id,
                )
            except:
                dets = None
            if dets is None:
                await ctx.send("You don't have any Easter 🥕 to spend yet!")
                return

            carrots: int = dets["carrots"]
            easter_fund = dets["easter_fund"]
            give_egg = False

            # Gleam Gems
            if option == "Gleam Gems":
                amount = random.randint(1, 25)
                if (carrots - 75) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 75
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + amount
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You gained {amount} <a:radiantgem:774866137472827432> Gleam Gems!"
                )
                return
            # Battle Multiplier
            if option == "Battle Mult.":
                if (carrots - 50) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 50
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["battle-multiplier"] = min(
                    inventory.get("battle-multiplier", 0) + 2, 50
                )
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id,
                )
                await ctx.send(f"You bought 2x Battle Multipliers.")
            # Shiny Multiplier
            if option == "Shiny Mult.":
                if (carrots - 50) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 50
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["shiny-multiplier"] = min(
                    inventory.get("shiny-multiplier", 0) + 2, 50
                )
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                    inventory,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id,
                )
                await ctx.send(f"You bought 2x Shiny Multipliers.")
            # Skin
            if option == "Easter Skin":
                if (carrots - 150) < 0:
                    await ctx.send("You don't have enough 🥕 carrots for that!")
                    return
                carrots -= 150
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id,
                )
                skins = await pconn.fetchval(
                    "SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id
                )
                pokemon = random.choice(list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "easter2023" not in skins[pokemon]:
                    skins[pokemon]["easter2023"] = 1
                else:
                    skins[pokemon]["easter2023"] += 1
                await pconn.execute(
                    "UPDATE users SET skins = $1::json WHERE u_id = $2",
                    skins,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You got a {pokemon.title()} Easter skin! Apply it with `/skin apply`."
                )
            # Fund
            if option == "Fund":
                if (carrots - 150) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                if easter_fund >= 25000:
                    await ctx.send(
                        "Congrats! You've maxed out your fund!\nPlease use `/easter buy option: Painted Egg` instead!!"
                    )
                    return
                if (easter_fund + 150) > 25000:
                    charge = 25000 - easter_fund
                    carrots -= charge
                    bonus_msg = f"\nYou've successfully added **{charge}** 🥕 to the Winter Fund, it is now Maxed!!"
                else:
                    charge = 150
                    carrots -= 150
                    bonus_msg = (
                        "\nYou've successfully added **150** 🥕 to the Winter Fund!"
                    )
                await pconn.execute(
                    "UPDATE events_new SET easter_fund = easter_fund + $1, carrots = $2 WHERE u_id = $3",
                    charge,
                    carrots,
                    ctx.author.id,
                )
                give_egg = True
            # Painted Egg
            if option == "Painted Egg":
                if (carrots - 50) < 0:
                    await ctx.send("You don't have enough 🥕 for that!")
                    return
                carrots -= 50
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                bonus_msg = "\nAlso gained **1 Redeem**!"
                give_egg = True

            if give_egg:
                # Check daycare
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
                    await ctx.send(
                        "You already have enough Pokemon in the Daycare!\nIncrease space with `/buy daycare`"
                    )
                    return

                # Remove carrots
                await pconn.execute(
                    "UPDATE events_new SET carrots = $1 WHERE u_id = $2",
                    carrots,
                    ctx.author.id,
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
                    color=0x00FF00,
                )
                embed.add_field(
                    name="Egg Details",
                    value=f"Diggersby has granted you a {emoji} {msg} **{ivpercent}** Painted Egg!\nIt'll hatch in **150** steps!",
                )
                embed.set_image(url="https://mewbot.xyz/eastereggs.png")
                embed.set_footer(
                    text="Easter 2023 ends on 4/23 | Make sure to join Mewbot Official for more Events!"
                )
                await ctx.send(embed=embed)

    # @easter.command(name="convert")
    async def easter_convert(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            old_dets = await pconn.fetchrow(
                "SELECT * FROM events WHERE u_id = $1 ORDER BY easter_fund DESC LIMIT 1",
                ctx.author.id,
            )
            converted = old_dets["converted"]
            if converted:
                await ctx.send("Sorry you've done this already!")
                return

            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                ctx.author.id,
            )
            await pconn.execute(
                f"UPDATE events_new SET carrots = carrots + $1 WHERE u_id = $2",
                old_dets["carrots"],
                ctx.author.id,
            )
            await pconn.execute(
                f"UPDATE events_new SET easter_fund = easter_fund + $1 WHERE u_id = $2",
                old_dets["easter_fund"],
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE events SET converted = True WHERE u_id = $1", ctx.author.id
            )
            await ctx.send("Successful")

    @commands.hybrid_group()
    async def summer(self, ctx: commands.Context): ...

    # @summer.command(name="info")
    async def summer_info(self, ctx):
        "Details about our Summer Event 2024."
        embed = discord.Embed(
            title="Mewbot Summer Event 2024",
            description="More details on the event and how things are working!",
            color=0x00FF00,
        )
        embed.add_field(
            name="Raids",
            value="Raids have arrived across Discord. They drop seashells 🐚 and can be used in the summer shop.",
            inline=False,
        )
        embed.add_field(
            name="Event Shop",
            value="Using various bot currency, you can unlock the event skins and different bot benefits. There are boosted versions of the skins available too",
            inline=False,
        )
        embed.add_field(
            name="Throwing Water Balloons",
            value="Earned by Breeding, Fishing, Mining, and Catching Spawns! You can hit other players with your earned water balloons <:waterballoon:1273431369749495930>! There is a slight chance you'll miss though.",
            inline=False,
        )
        embed.add_field(
            name="Water Ballon Rewards",
            value="There will be several rewards for water balloons. At 100 thrown you get the <@&1273432534239285288> and at 250 thrown you'll get the choice of trainer image! We also plan on a bot wide reward that changes the more water balloons thrown!!",
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/998291646443704320/1273461543543242816/Screenshot_2024-08-14_220100-removebg-preview.png?ex=66beb2fb&is=66bd617b&hm=2a01e545b315c1589a6ed0bceff6716e51812bccc5f78af126b23fb9f86d1287&"
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/998291646443704320/1273460655109832755/Untitled_1.png?ex=66beb227&is=66bd60a7&hm=ed17029fbcc7f073f48e5647f0e5752fd6ce033bbd1c2435f7febd7472aa2555&"
        )
        await ctx.send(embed=embed)

    # @summer.command(name="items")
    async def summer_items(self, ctx):
        """Check your summer inventory."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Not available at the moment!")
        # return
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the summer season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchrow(
                "SELECT snowballs, seashells FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
        embed = discord.Embed(
            title=f"{ctx.author.name.title()}'s Summer Items",
            description=f"These are all items that are related to the event.\nGet these items from Raids, Catching, Breeding, Fishing and Mining!",
            color=0x0084FD,
        )
        embed.add_field(
            name="Items",
            value=(
                f"**Water Balloons**: {inventory['snowballs']}x <:waterballoon:1273431369749495930>\n"
                f"**Seashells**: {inventory['seashells']}x 🐚"
            ),
            inline=False,
        )
        embed.set_footer(text="Remember, touch grass!")
        await ctx.send(embed=embed)

    # @summer.command(name="shop")
    async def summer_shop(self, ctx):
        """Check the summer shop."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Not available at the moment!")
        # return
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the summer season!")
            return

        embed = discord.Embed(
            title="Summer Event Shop",
            description="Make sure to fish, mine, and catch Pokemon to maximize Water Balloons <:waterballoon:1273431369749495930>!\nJoin our Official Server and grab the role! `/invite`",
            color=0x0084FD,
        )
        embed.add_field(
            name="Account Multipliers",
            value=(
                "`1.` __2x Battle Multi.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
                "`2.` __2x Shiny Multi.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
                "`3.` __2x Breeding Multi.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Currencies",
            value=(
                "`4.` __1-25 Gleam Gems.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\nLimited to 1000 daily."
            ),
            inline=False,
        )
        embed.add_field(
            name="Gleams",
            value=(
                "`5.` __Event Skin__\n**Cost:** 150 <a:radiantgem:774866137472827432>\nThis is a skin that goes into inventory.\n"
                "`6.` __Boosted Event Skin__\n**Cost:** 300 <a:radiantgem:774866137472827432>\nThis is a Pokemon already with the skin equipped."
            ),
            inline=False,
        )
        embed.add_field(
            name="Seashells 🐚",
            value=(
                "`7.` __NPC Energy__\n**Cost:** 50 🐚\nIs applied right away. Can't have more than 50 energy stored.\n"
                "`8.` __Random Chest__\n**Cost:** 150 🐚\nCommon, Rare, or Mythic. Limited to 20 daily.\n"
                "`9.` __Shadow Streak__\n**Cost:** 300 🐚\nIncreases <:shadow:1010559067590246410> by 50. Limited to 10 daily.\n"
            ),
        )
        embed.set_footer(text="Use /summer buy to buy an item!")
        await ctx.send(embed=embed)

    # @summer.command(name="buy")
    async def summer_buy(
        self,
        ctx,
        pack: Literal[
            "1. 2x Battle Multi.",
            "2. 2x Shiny Multi.",
            "3. 2x Breeding Multi.",
            "4. 1-25 Gleam Gems",
            "5. Event Gleam",
            "6. Boosted Event Gleam",
            "7. NPC Energy",
            "8. Random Chest",
            "9. Shadow Streak",
        ],
    ):
        """Buy something from the summer shop."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Not available at the moment!")
        # return
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the summer season!")
            return
        option = int(pack[0])
        if option < 1 or option > 9:
            await ctx.send("That is not a valid option number.")
            return
        if ctx.author.id in self.purchaselock:
            await ctx.send("Please finish any pending purchases!")
            return

        async with self.bot.db[0].acquire() as pconn:
            credits, redeems, npc_energy = await pconn.fetchrow(
                "SELECT mewcoins, redeems, npc_energy FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if credits is None:
                await ctx.send(
                    "You haven't started! Please use `/start` to start your adventure!"
                )
                return

            (
                radiant_gems,
                battle_multiplier,
                shiny_multiplier,
                breeding_multiplier,
            ) = await pconn.fetchrow(
                "SELECT radiant_gem, battle_multiplier, shiny_multiplier, breeding_multiplier FROM account_bound WHERE u_id = $1",
                ctx.author.id,
            )
            if radiant_gems is None:
                await ctx.send(
                    "No bound items table found. Have you started or converted to the new bag system if needed?"
                )
                return

            gleam_limit = await pconn.fetchrow(
                "SELECT seashells, event_limit, radiant_limit, gleam_limit FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
            if gleam_limit is None:
                # Try to add user to table and then have them redo the command
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    ctx.author.id,
                )
                await ctx.send("Please retry the command.")
                return

            seashells = gleam_limit["seashells"]
            event_limit = gleam_limit["event_limit"]
            radiant_limit = gleam_limit["radiant_limit"]
            gleam_limit = gleam_limit["gleam_limit"]

            self.purchaselock.append(ctx.author.id)

            # Battle Multiplier
            if option == 1:
                if credits < 50000:
                    await ctx.send("You don't have enough credits for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if battle_multiplier >= 50:
                    await ctx.send("Your Battle Multiplier is already maxed out!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                battle_multiplier = min(battle_multiplier + 2, 50)
                await pconn.execute(
                    "UPDATE account_bound SET battle_multiplier = $1 WHERE u_id = $2",
                    battle_multiplier,
                    ctx.author.id,
                )
                await ctx.send("You have successfully purchased 2x Battle Multiplier!")
                self.purchaselock.remove(ctx.author.id)
                return

            # Shiny Multiplier
            if option == 2:
                if credits < 50000:
                    await ctx.send("You don't have enough credits for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if shiny_multiplier >= 50:
                    await ctx.send("Your Shiny Multiplier is already maxed out!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                shiny_multiplier = min(shiny_multiplier + 2, 50)
                await pconn.execute(
                    "UPDATE account_bound SET shiny_multiplier = $1 WHERE u_id = $2",
                    shiny_multiplier,
                    ctx.author.id,
                )
                await ctx.send("You have successfully purchased 2x Shiny Multiplier!")
                self.purchaselock.remove(ctx.author.id)
                return

            # Breeding Multiplier
            if option == 3:
                if credits < 50000:
                    await ctx.send("You don't have enough credits for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if breeding_multiplier >= 50:
                    await ctx.send("Your Breeding Multiplier is already maxed out!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                breeding_multiplier = min(breeding_multiplier + 2, 50)
                await pconn.execute(
                    "UPDATE account_bound SET breeding_multiplier = $1 WHERE u_id = $2",
                    breeding_multiplier,
                    ctx.author.id,
                )
                await ctx.send(
                    "You have successfully purchased 2x Breeding Multiplier!"
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Gleam Gems
            if option == 4:
                if gleam_limit >= 1000:
                    await ctx.send("You have hit the daily purchase limit!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if credits < 50000:
                    await ctx.send("You don't have enough credits for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                earned_gleams = random.randint(1, 25)
                new_limit = gleam_limit + earned_gleams
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = radiant_gem + $1 WHERE u_id = $2",
                    earned_gleams,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET gleam_limit = $1 WHERE u_id = $2",
                    new_limit,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You bought {earned_gleams}x Gleam Gems <a:radiantgem:774866137472827432>.\n"
                    f"You have purchased {new_limit}, the limit is 1000 per day."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Event Gleams
            # Gives the skin for the Pokemon rather than the Pokemon
            if option == 5:
                if radiant_gems < 150:
                    await ctx.send(
                        "You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!"
                    )
                    self.purchaselock.remove(ctx.author.id)
                    return
                radiant_gems -= 150
                skins = await pconn.fetchval(
                    "SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id
                )
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "summer2024" not in skins[pokemon]:
                    skins[pokemon]["summer2024"] = 1
                else:
                    skins[pokemon]["summer2024"] += 1
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = $1 WHERE u_id = $2",
                    radiant_gems,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE users SET skins = $1::json WHERE u_id = $2",
                    skins,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You got a **{pokemon.title()} Summer Skin**! Apply it with `/skin apply`."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Boosted Event Glems
            # This gives Pokemon w/skin rather than just skin
            if option == 6:
                if radiant_gems < 300:
                    await ctx.send(
                        "You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!"
                    )
                    self.purchaselock.remove(ctx.author.id)
                    return
                radiant_gems -= 300
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = $1 WHERE u_id = $2",
                    radiant_gems,
                    ctx.author.id,
                )
                await ctx.bot.commondb.create_poke(
                    ctx.bot,
                    ctx.author.id,
                    pokemon.capitalize(),
                    boosted=True,
                    skin="summer2024",
                )
                await ctx.send(
                    f"You got a **{pokemon.title()} Summer Pokemon**!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # NPC Energy
            if option == 7:
                if npc_energy >= 50:
                    await ctx.send("Go spend some energy first!")
                    return
                if seashells < 50:
                    await ctx.send("You don't have enough seashells 🐚 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                seashells -= 50
                await pconn.execute(
                    "UPDATE events_new SET seashells = $1 WHERE u_id = $2",
                    seashells,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE users SET npc_energy = npc_energy + 2 WHERE u_id = $1",
                    ctx.author.id,
                )
                self.purchaselock.remove(ctx.author.id)
                await ctx.send(
                    f"You received some **NPC Energy**!\nIt's been added to your current amount."
                )

            # Random Chest
            if option == 8:
                if event_limit >= 20:
                    await ctx.send("You have hit the daily purchase limit!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if seashells < 150:
                    await ctx.send("You don't have enough seashells 🐚 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                seashells -= 150
                new_limit = event_limit + 1
                chest_choice = random.choices(
                    ("mythic_chest", "rare_chest", "common_chest"),
                    weights=(0.40, 0.40, 0.20),
                )[0]
                await ctx.bot.commondb.add_bag_item(
                    ctx.author.id, chest_choice, 1, True
                )
                await pconn.execute(
                    "UPDATE events_new SET seashells = $1, event_limit = event_limit + 1 WHERE u_id = $2",
                    seashells,
                    ctx.author.id,
                )
                fancy_name = chest_choice.replace("_", " ").title()
                self.purchaselock.remove(ctx.author.id)
                await ctx.send(
                    f"You received a {fancy_name}!\n"
                    f"You have purchased {new_limit} chests, the limit is 20 per day."
                )

            # Shadow Streak
            if option == 9:
                if radiant_limit >= 10:
                    await ctx.send("You have hit the daily purchase limit!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if seashells < 300:
                    await ctx.send("You don't have enough seashells 🐚 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                seashells -= 300
                new_limit = radiant_limit + 1
                await pconn.execute(
                    "UPDATE users SET chain = chain + 50 WHERE u_id = $1", ctx.author.id
                )
                await pconn.execute(
                    "UPDATE events_new SET seashells = $1, radiant_limit = radiant_limit + 1 WHERE u_id = $2",
                    seashells,
                    ctx.author.id,
                )
                self.purchaselock.remove(ctx.author.id)
                await ctx.send(
                    f"You received x50 Shadow Streak <:shadow:1010559067590246410>!\n"
                    f"You have purchased {new_limit} <:shadow:1010559067590246410>, the limit is 10 per day."
                )

    # @summer.command(name="wb")
    async def water_balloon(self, ctx, amount: int, player: discord.Member):
        "Throw a water balloon at another member."
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the summer season!")
            return
        if ctx.author.id == player.id:
            await ctx.send("Why hit yourself? Hit a friend... or enemy!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            msg = ""
            (
                snowballs,
                times_hit,
                times_thrown,
                trainer_redeemed,
                role_redeemed,
            ) = await pconn.fetchrow(
                "SELECT snowballs, times_hit, times_thrown, trainer_redeemed, role_redeemed FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
            if snowballs is None:
                await ctx.send("You have not started the event!")
                return
            elif snowballs < 1:
                await ctx.send(
                    "You have to get some water balloons! <:waterballoon:1273431369749495930>!"
                )
                return
            attacked_times_hit = await pconn.fetchval(
                "SELECT times_hit FROM events_new WHERE u_id = $1", player.id
            )
            if attacked_times_hit is None:
                # Meaning player hit hasn't started event
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    player.id,
                )
                await ctx.send("Please try this command again shortly...")
                return
            snowballs -= amount
            if snowballs < 0:
                await ctx.send("You don't have enough waterballoons for that throw!")
                return
            successful_hits = 0
            unsuccessful_hits = 0
            for i in range(amount):
                if random.randint(1, 100) <= 35:
                    unsuccessful_hits += 1
                else:
                    successful_hits += 1
                times_thrown += 1

            # Process hits
            await pconn.execute(
                "UPDATE events_new SET snowballs = $1, times_thrown = $2 WHERE u_id = $3",
                snowballs,
                times_thrown,
                ctx.author.id,
            )
            # Let's hit player
            await pconn.execute(
                "UPDATE events_new SET times_hit = times_hit + $1 WHERE u_id = $2",
                successful_hits,
                player.id,
            )
            # Process rewards, role only in Official.
            if ctx.guild.id == 998128574898896906:
                if times_thrown >= 100 and role_redeemed is False:
                    event_role = ctx.guild.get_role(1273432534239285288)
                    await ctx.author.add_roles(
                        event_role, reason=f"Event threshold reward - {ctx.author}"
                    )
                    await pconn.execute(
                        "UPDATE events_new SET role_redeemed = True WHERE u_id = $1",
                        ctx.author.id,
                    )
                    msg += "You've received the Summer Event '24 Official Server Role!"
            if times_thrown >= 250:
                if trainer_redeemed:
                    pass
                else:
                    choice = await ListSelectView(
                        ctx, "Please choose a trainer image!"
                    ).wait()
                    if choice is None:
                        await ctx.send("You did not select in time, cancelling.")
                        self.purchaselock.remove(ctx.author.id)
                        return
                    trainer_images = await pconn.fetchval(
                        "SELECT trainer_images::json FROM account_bound WHERE u_id = $1",
                        ctx.author.id,
                    )
                    choice = str(choice)
                    category = "summer"
                    if category not in trainer_images:
                        trainer_images[category] = {}
                    if choice not in trainer_images[category]:
                        trainer_images[category][choice] = 1
                    else:
                        trainer_images[category][choice] += 1
                    await pconn.execute(
                        "UPDATE account_bound SET trainer_images = $1::json WHERE u_id = $2",
                        trainer_images,
                        ctx.author.id,
                    )
                    await pconn.execute(
                        "UPDATE events_new SET trainer_redeemed = True WHERE u_id = $1",
                        ctx.author.id,
                    )
                    msg += f"You've successfully redeemed {choice} as your trainer image!\nIt's been added to your trainer image inventory."

        embed = discord.Embed(
            title="Mewbot Summer 2024",
            description=f"You've throw a water balloon <:waterballoon:1273431369749495930>\nDid you hit your mark?!",
            color=0x0084FD,
        )
        embed.add_field(
            name="Victim",
            value=(
                f"You've hit **{player.name} {successful_hits} times**!\n"
                f"You missed {unsuccessful_hits} times though..."
            ),
            inline=False,
        )
        embed.add_field(
            name=f"{ctx.author.name}'s Stats",
            value=f"You've been hit __{times_hit} times__.\nYou've thrown __{times_thrown}__ water balloons!",
            inline=False,
        )
        if msg != "":
            embed.add_field(name="Rewards", value=f"{msg}", inline=False)
        embed.set_footer(text=f"You have {snowballs} water balloons remaining.")
        await ctx.send(embed=embed)

    # @commands.hybrid_group()
    async def valentine(self, ctx):
        """Valentine Commands."""
        pass

    # @valentine.command(name="buddy")
    async def buddy(self, ctx, member: discord.Member):
        """Choose a buddy for event"""
        # User can't participate in event
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
                "SELECT valentine FROM users WHERE u_id = $1", ctx.author.id
            )
            if check != 0:
                await ctx.send("You've already selected your Valentine Buddy!")
                return
            await pconn.execute(
                "UPDATE users SET valentine = $1 WHERE u_id = $2",
                member.id,
                ctx.author.id,
            )
        await ctx.send("You've successfully selected your Valentine's Buddy!")

    # @valentine.command(name="shop")
    async def valentine_shop(self, ctx):
        """Check the valentine shop."""
        if not self.VALENTINE_COMMANDS:
            await ctx.send("This command can only be used during the valentine season!")
            return
        # User can't participate in event
        if ctx.author.id == 1075429458271547523:
            return
        async with self.bot.db[0].acquire() as pconn:
            heart_amount = await pconn.fetchval(
                "SELECT hearts FROM users WHERE u_id = $1", ctx.author.id
            )
        embed = discord.Embed(
            title="Valentine Shop",
            description=f"Use <:poke_heart:1075152203297341482> Hearts gained from Raids to purchase items.\nYou have {heart_amount} <:poke_heart:1075152203297341482> Hearts",
            color=random.choice(RED_GREEN),
        )
        embed.add_field(
            name="Currency",
            value="`1.` 3 Redeems\n30 <:poke_heart:1075152203297341482>\n`2.` 1-25 Gleam Gems\n75 <:poke_heart:1075152203297341482>",
            inline=True,
        )
        embed.add_field(
            name="Multipliers",
            value="`3.` 2x Battle Multi\n50 <:poke_heart:1075152203297341482>\n`4.` 2x Shiny Multi\n50 <:poke_heart:1075152203297341482>",
            inline=True,
        )
        embed.add_field(
            name="Misc",
            value="`5.` 1 Raffle Entry\n100 <:poke_heart:1075152203297341482>\n`6.` Random Valentine Skin\n100 <:poke_heart:1075152203297341482>",
            inline=True,
        )
        embed.set_footer(
            text="Use /valentine buy with an option number to buy that item!"
        )
        await ctx.send(embed=embed)

    # @valentine.command(name="buy")
    async def valentine_buy(self, ctx, option: int):
        """Buy something from the valentine shop."""
        if not self.VALENTINE_COMMANDS:
            await ctx.send("This command can only be used during the valentine season!")
            return
        # User can't participate in event
        if ctx.author.id == 1075429458271547523:
            return
        if option < 1 or option > 6:
            await ctx.send(
                "That isn't a valid option. Select a valid option from `/valentine shop`."
            )
            return
        async with self.bot.db[0].acquire() as pconn:
            holidayinv = await pconn.fetchval(
                "SELECT hearts FROM users WHERE u_id = $1", ctx.author.id
            )
            if holidayinv == 0:
                await ctx.send("You haven't gotten any hearts yet!")
                return
            if option == 1:
                if holidayinv < 30:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 30
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + 3, hearts = $1 WHERE u_id = $2",
                    holidayinv,
                    ctx.author.id,
                )
                await ctx.send("You bought 3 Redeems.")
            if option == 2:
                amount = random.randint(1, 25)
                if holidayinv < 75:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 75
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["radiant gem"] = inventory.get("radiant gem", 0) + amount
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json,  hearts = $2 WHERE u_id = $3",
                    inventory,
                    holidayinv,
                    ctx.author.id,
                )
                await ctx.send(f"You bought {amount}x gleam gem.")
            if option == 3:
                if holidayinv < 50:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 50
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["battle-multiplier"] = min(
                    inventory.get("battle-multiplier", 0) + 2, 50
                )
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json, hearts = $2 WHERE u_id = $3",
                    inventory,
                    holidayinv,
                    ctx.author.id,
                )
                await ctx.send(f"You bought 2x Battle Multipliers.")
            if option == 4:
                if holidayinv < 50:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 50
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
                )
                inventory["shiny-multiplier"] = min(
                    inventory.get("shiny-multiplier", 0) + 2, 50
                )
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json, hearts = $2 WHERE u_id = $3",
                    inventory,
                    holidayinv,
                    ctx.author.id,
                )
                await ctx.send(f"You bought 2x Shiny Multipliers.")
            if option == 5:
                if holidayinv < 100:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 100
                await pconn.execute(
                    "UPDATE users SET raffle = raffle + 1, hearts = $1 WHERE u_id = $2",
                    holidayinv,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You were given an entry into the Valentine Raffle!\nThe raffle will be drawn in the Mewbot Official Server. `\invite`"
                )
            if option == 6:
                if holidayinv < 100:
                    await ctx.send("You don't have enough hearts for that!")
                    return
                holidayinv -= 100
                skins = await pconn.fetchval(
                    "SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id
                )
                pokemon = random.choice(list(self.CHRISTMAS_MOVES.keys())).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "valentines2023" not in skins[pokemon]:
                    skins[pokemon]["valentines2023"] = 1
                else:
                    skins[pokemon]["valentines2023"] += 1
                await pconn.execute(
                    "UPDATE users SET skins = $1::json, hearts = $2 WHERE u_id = $3",
                    skins,
                    holidayinv,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You got a {pokemon} valentine skin! Apply it with `/skin apply`."
                )

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
            await ctx.send(
                "That isn't a valid option. Select a valid option from `/halloween shop`."
            )
            return
        async with self.bot.db[0].acquire() as pconn:
            bal = await pconn.fetchrow(
                "SELECT candy, potion, pumpkin FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
            bal = dict(bal)
            if bal is None:
                await ctx.send("You haven't gotten any halloween treats to spend yet!")
                return
            # Convert 50 candy for 1 potion
            if option == 1:
                if bal["candy"] < 50:
                    await ctx.send("You don't have enough Candy for that!")
                    return
                await pconn.execute(
                    "UPDATE events_new SET candy = candy - 50, potion = potion + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await ctx.send(
                    "Successfully bought 1 <:potion:1301436846307540992> for 50 :candy: ."
                )
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
                    await ctx.send("Successfully bought a raffle ticket for 1 <:pumpkin:1301436707169894430>!")
                return"""
            # Replaces the above while we don't offer those options
            # Raffle entry
            if option == 3:
                if bal["pumpkin"] < 1:
                    await ctx.send("You don't have enough Pumpkins for that!")
                    return
                await pconn.execute(
                    "UPDATE events_new SET pumpkin = pumpkin - 1, raffle = raffle + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await ctx.send(
                    "Successfully bought a raffle ticket for 1 <:pumpkin:1301436707169894430>!"
                )
                return
            # Everything from this point below uses Potions as currency
            # Checks balance per price as below.
            price = [50, 8, 2, 5, 10][option - 2]
            if bal["potion"] < price:
                await ctx.send(
                    "You don't have enough <:potion:1301436846307540992> for that!"
                )
                return
            await pconn.execute(
                "UPDATE events_new SET potion = potion - $2 WHERE u_id = $1",
                ctx.author.id,
                price,
            )
            # Convert potions for mask
            if option == 2:
                await pconn.execute(
                    "UPDATE events_new SET pumpkin = pumpkin + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought 1 <:pumpkin:1301436707169894430> for {price} <:potion:1301436846307540992>."
                )
            # Spooky Chest
            if option == 4:
                await pconn.execute(
                    "UPDATE events_new SET spooky_chest = spooky_chest + $1 WHERE u_id = $2",
                    1,
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought a Spooky Chest for {price} <:potion:1301436846307540992>."
                )
            # Fleshy Chest
            elif option == 5:
                await pconn.execute(
                    "UPDATE events_new SET fleshy_chest = fleshy_chest + $1 WHERE u_id = $2",
                    1,
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought a Fleshy Chest for {price} <:potion:1301436846307540992>."
                )
            # Horrific Chest
            elif option == 6:
                await pconn.execute(
                    "UPDATE events_new SET horrific_chest = horrific_chest + $1 WHERE u_id = $2",
                    1,
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought a Horrific Chest for {price} <:potion:1301436846307540992>."
                )

    @halloween.command(name="inventory")
    async def halloween_inventory(self, ctx):
        """Check your halloween inventory."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT candy, potion, pumpkin, spooky_chest, fleshy_chest, horrific_chest, raffle FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
        if data is None:
            await ctx.send("You haven't gotten any halloween treats yet!")
            return
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Halloween Inventory",
            description=f"Use `/halloween shop` to see what you can spend your treats on!\nYou have {data['raffle']} raffle entries!",
            color=ORANGE,
        )
        embed.add_field(
            name="Bag of Treats",
            value=(
                f"{data['candy']}x Candy :candy: \n"
                f"{data['potion']}x Sus Potions <:potion:1301436846307540992>\n"
                f"{data['pumpkin']}x Mystery Pumpkins <:pumpkin:1301436707169894430>\n"
            ),
            inline=True,
        )
        embed.add_field(
            name="Chests",
            value=(
                f"{data['spooky_chest']}x Spooky\n"
                f"{data['fleshy_chest']}x Fleshy\n"
                f"{data['horrific_chest']}x Horrific\n"
            ),
            inline=True,
        )

        embed.set_footer(text="Join Mewbot's Official Server for all event updates!")
        await ctx.send(embed=embed)

    @halloween.group(name="pumpkin")
    async def pumpkin(self, ctx): ...

    @pumpkin.command(name="pop")
    async def pumpkin_pop(self, ctx):
        """Open a mysterious pumpkin and receive a reward... or a trick!"""

        # Starting message with suspense
        # if not self.HALLOWEEN_COMMANDS:
        #     await ctx.send("This command can only be used during the halloween season!")
        #     return
        embed = discord.Embed(
            title="🎃 Selected a Mysterious pumpkin from your stash! 🎃",
            description="*Do you dare to open it?*",
            color=discord.Color.orange(),
        )
        open_button = discord.ui.Button(
            label="Pop Pumpkin", style=discord.ButtonStyle.green
        )

        # Callback for the button to handle opening the pumpkin
        async def open_callback(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(
                    "Only the pumpkin owner can open it!", ephemeral=True
                )
                return

            # Random rewards with suspense delay
            rewards = {
                "candy": (0.35, "🍬 A stash of candies and potions spills out!"),
                "potion": (0.15, "🧪 You found a precious potion!"),
                "shadow_streak": (
                    0.25,
                    "🌌 A mysterious shadow aura swirls out, granting you 150 Shadow Streak!",
                ),
                "trick": (
                    0.25,
                    "💀 A ghostly hand reaches out and gives you a fright! (You were tricked!)",
                ),
            }
            reward = random.choices(
                list(rewards.keys()), weights=[v[0] for v in rewards.values()], k=1
            )[0]
            message = rewards[reward][1]

            # Get user pumpkin count
            async with self.bot.db[0].acquire() as pconn:
                try:
                    pumpkins = await pconn.fetchval(
                        "UPDATE events_new SET pumpkin = pumpkin - 1 WHERE u_id = $1 RETURNING pumpkin",
                        ctx.author.id,
                    )
                except:
                    await ctx.send(
                        embed=make_embed(
                            title="You probably don't have any <:pumpkin:1301436707169894430>"
                        )
                    )
                    return

                # if they have more than 5 pumpkins, there should be a 60% chance of event pokemon,
                # if not, there should be a 90% chance
                if pumpkins >= 5:
                    true_reward = random.choices(
                        ("event_pokemon", "reward"), weights=(0.6, 0.4), k=1
                    )[0]
                else:
                    true_reward = random.choices(
                        ("event_pokemon", "reward"), weights=(0.9, 0.1), k=1
                    )[0]
                if true_reward == "event_pokemon":
                    pokemon = random.choice(self.EVENT_POKEMON).lower()
                    await ctx.bot.commondb.create_poke(
                        ctx.bot,
                        ctx.author.id,
                        pokemon.capitalize(),
                        skin="halloween2024",
                    )
                    pokeurl = "http://mewbot.xyz/sprites/" + await get_file_name(
                        pokemon, ctx.bot, skin="halloween2024"
                    )
                    guild = await ctx.bot.mongo_find(
                        "guilds", {"id": ctx.channel.guild.id}
                    )
                    if guild is None:
                        small_images = False
                    else:
                        small_images = guild["small_images"]
                    embed = discord.Embed(
                        title="🎃 *A Halloween Pokémon Jumps Out!* 🎃",
                        description="As you pry open the pumpkin, mist swirls out and...\n\n"
                        "👻 *A Halloween Pokémon appears!* \n\n"
                        "The Pokémon has been added to your inventory!",
                        color=discord.Color.purple(),
                    )
                    embed.set_thumbnail(
                        url=pokeurl
                    )  # Replace with the actual Pokémon image URL
                    embed.set_footer(
                        text="Happy Halloween! Keep opening pumpkins for more surprises."
                    )

                    if small_images:
                        embed.set_thumbnail(url=pokeurl)
                    else:
                        embed.set_image(url=pokeurl)
                    await interaction.response.edit_message(embed=embed, view=None)

                else:
                    if reward == "shadow_streak":
                        await pconn.execute(
                            "UPDATE users SET chain = chain + 50 WHERE u_id = $1",
                            ctx.author.id,
                        )
                    elif reward == "candy":
                        await self.give_candy(ctx, 500)
                    elif reward == "potion":
                        await self.drop_potions(ctx)

                    embed = discord.Embed()
                    embed.title = "🎃 You opened the pumpkin!"
                    embed.description = message
                    await interaction.response.edit_message(embed=embed, view=None)

        # Attach the callback to the button
        open_button.callback = open_callback
        view = discord.ui.View()
        view.add_item(open_button)

        # Send the initial message with the button
        await ctx.send(embed=embed, view=view)

    @halloween.command(name="shop")
    async def halloween_shop(self, ctx):
        """Check the halloween shop."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        # desc = (
        # "**Option# | Price | Item**\n"
        # "**1** | 50 candy | 1 Sus Potion\n"
        # "**2** | 5 Potions | Spooky Chest\n"
        # "**3** | 25 Potions | Fleshy Chest\n"
        # "**4** | 80 Potions | Horrific Chest\n"
        # "**5** | 150 Potions | 1 pumpkin\n"
        # "**6** | 1 Mask | Missingno\n"
        # "**7** | 1 Mask | Halloween radiant\n"
        # "**8** | 1 Mask | 1 Halloween raffle entry\n"
        # )
        embed = discord.Embed(
            title="Halloween Shop",
            color=ORANGE,
            description="Spend your Potions <:potion:1301436846307540992> and Candies :candy:. Use /halloween buy with an option number to buy that item!",
        )
        embed.add_field(
            name="1. Sus Potion <:potion:1301436846307540992>",
            value="50 :candy: ",
            inline=True,
        )
        embed.add_field(
            name="2. Pumpkin <:pumpkin:1301436707169894430>",
            value="50 <:potion:1301436846307540992>",
            inline=True,
        )
        embed.add_field(
            name="3. Raffle Entry",
            value="1 <:pumpkin:1301436707169894430>",
            inline=True,
        )
        embed.add_field(
            name="4. Spooky Chest",
            value="2 <:potion:1301436846307540992>",
            inline=True,
        )
        embed.add_field(
            name="5. Fleshy Chest",
            value="5 <:potion:1301436846307540992>",
            inline=True,
        )
        embed.add_field(
            name="6. Horrific Chest",
            value="10 <:potion:1301436846307540992>",
            inline=True,
        )
        # embed.add_field(
        # name="7. Missingno",
        # value="1 <:pumpkin:1301436707169894430>",
        # inline=True
        # )
        # embed.add_field(
        # name="8. Halloween Radiant",
        # value="1 <:pumpkin:1301436707169894430>",
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
            spooky_chest = await pconn.fetchval(
                "SELECT spooky_chest FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if spooky_chest is None:
                await ctx.send(f"You do not have any Spooky Chest!")
                return
            if spooky_chest <= 0:
                await ctx.send("You do not have any Spooky Chests!")
                return
            await pconn.execute(
                "UPDATE events_new SET spooky_chest = spooky_chest - 1 where u_id = $1",
                ctx.author.id,
            )
            reward = random.choices(
                ("missingno", "potion", "candy", "trick"),
                weights=(0.18, 0.12, 0.3, 0.4),
            )[0]
            if reward == "gleam":
                # Chance of Zoroark trick
                chance_int = random.randint(1, 100)
                if chance_int > 90:
                    pokemon = "Zoroark"
                    msg = f"**Trick!** You received a **{pokemon}!**\n"
                    skin = None
                else:
                    pokemon = random.choice(self.HALLOWEEN_RADIANT)
                    msg = f"**Treat!** You received a Halloween **{pokemon}!**\n"
                    skin = "halloween2023"
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, skin=skin
                )
            # Redeems removed as event rewards
            # elif reward == "redeem":
            # amount = random.randint(1, 3)
            # async with ctx.bot.db[0].acquire() as pconn:
            # await pconn.execute(
            # "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
            # amount,
            # ctx.author.id,
            # )
            # msg = f"You received {amount} redeem!\n"
            elif reward == "candy":
                await self.give_candy(ctx, 150)
                return
            elif reward == "potion":
                await self.drop_potions(ctx)
                return
            elif reward == "missingno":
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Missingno")
                msg = f"You received a Missingno!\n"
            elif reward == "trick":
                await ctx.send(
                    "*Trick or treat?*\nI choose trick!\n*A ghost flies out of the empty box*"
                )
                return
        candy = random.randint(1, 3)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE events_new SET candy = candy + $1 WHERE u_id = $2",
                candy,
                ctx.author.id,
            )
        msg += f"You also received {candy} :candy: !\n"
        await ctx.send(embed=make_embed(title=msg))

    @halloween.command(name="open_fleshy")
    async def open_fleshy(self, ctx):
        """Open a fleshy chest."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            fleshy_chest = await pconn.fetchval(
                "SELECT fleshy_chest FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if fleshy_chest is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if fleshy_chest <= 0:
                await ctx.send("You do not have any Fleshy Chests!")
                return
            await pconn.execute(
                "UPDATE events_new SET fleshy_chest = fleshy_chest - 1 where u_id = $1",
                ctx.author.id,
            )
            reward = random.choices(
                ("candy", "potion", "rarechest", "mythicchest", "missingno", "trick"),
                weights=(0.35, 0.15, 0.10, 0.05, 0.20, 0.15),
            )[0]

            if reward == "gleam":
                # Chance of Zoroark trick
                chance_int = random.randint(1, 100)
                if chance_int > 90:
                    pokemon = "Zoroark"
                    msg = f"**Trick!** You received a **{pokemon}!**\n"
                    skin = None
                else:
                    pokemon = random.choice(self.HALLOWEEN_RADIANT)
                    msg = f"**Treat!** You received a Halloween **{pokemon}!**\n"
                    skin = "halloween2023"
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, skin=skin
                )
            elif reward == "candy":
                await self.give_candy(ctx, 300)
                return
            elif reward == "potion":
                await self.drop_potions(ctx, random.randint(5, 8))
                return

            elif reward == "mythicchest":
                await ctx.bot.commondb.add_bag_item(
                    ctx.author.id, "mythic_chest", 1, True
                )
                msg = "You received a Mythic Chest!\n"

            elif reward == "rarechest":
                await ctx.bot.commondb.add_bag_item(
                    ctx.author.id, "rare_chest", 1, True
                )
                msg = "You received a Rare Chest!\n"

            elif reward == "missingno":
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Missingno")
                msg = f"You received a Missingno!\n"

            elif reward == "trick":
                await ctx.send(
                    "*Trick or treat?*\nI choose trick!\n*A ghost flies out of the empty box*"
                )
                return
        potions = random.randint(1, 3)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE events_new SET potion = potion + $1 WHERE u_id = $2",
                potions,
                ctx.author.id,
            )
        msg += f"You also received {potions} <:potion:1301436846307540992>!\n"
        await ctx.send(msg)

    @halloween.command(name="open_horrific")
    async def open_horrific(self, ctx):
        """Open a horrific chest."""
        if not self.HALLOWEEN_COMMANDS:
            await ctx.send("This command can only be used during the halloween season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            horrific_chest = await pconn.fetchval(
                "SELECT horrific_chest FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if horrific_chest is None:
                await ctx.send(f"You do not have any Horrific Chests!")
                return
            if horrific_chest <= 0:
                await ctx.send("You do not have any Horrific Chests!")
                return
            await pconn.execute(
                "UPDATE events_new SET horrific_chest = horrific_chest - 1 where u_id = $1",
                ctx.author.id,
            )
            reward = random.choices(
                ("streak", "pumpkin", "trick"),
                weights=(0.35, 0.20, 0.45),
            )[0]
            if reward == "streak":

                # Chance of Zoroark trick
                #     chance_int = random.randint(1, 100)
                #     if chance_int > 90:
                #         pokemon = 'Zoroark'
                #         boosted = False
                #         msg = f"**Trick!** You received a **{pokemon}!**\n"
                #         shiny = False
                #     else:
                #         pokemon = random.choice(await self.get_ghosts())
                #         boosted = True
                #         msg = f"**Treat!** You received a Shiny Boosted **{pokemon}!**\n"
                #         shiny = True
                #     await ctx.bot.commondb.create_poke(
                #         ctx.bot, ctx.author.id, pokemon, boosted=boosted, shiny=shiny
                #     )
                # if option == 9:
                await pconn.execute(
                    "UPDATE users SET chain = chain + 50 WHERE u_id = $1", ctx.author.id
                )
                await ctx.send(
                    f"You received x50 Shadow Streak <:shadow:1010559067590246410>!\n"
                )
                return

            elif reward == "pumpkin":
                await self.give_pumpkin(ctx.author, 1)

                await ctx.send(
                    embed=make_embed(
                        title="🎉 You found the treat!",
                        description=self.rand_bag_text(),
                    )
                )
                return
            elif reward == "legendchest":
                await ctx.bot.commondb.add_bag_item(
                    ctx.author.id, "legend_chest", 1, True
                )
                msg = "You received a Legend Chest!\n"
            elif reward == "trick":
                await ctx.send(
                    "*Trick or treat?*\nI choose trick!\n*A ghost flies out of the empty box*"
                )
                return
            await pconn.execute(
                "UPDATE events_new SET horrific_chest = horrific_chest - 1 where u_id = $1",
                ctx.author.id,
            )
        potions = random.randint(1, 5)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE events_new SET potion = potion + $1 WHERE u_id = $2",
                potions,
                ctx.author.id,
            )
        msg += f"You also received {potions} <:potion:1301436846307540992>!\n"
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
                await ctx.send(
                    "There is already honey in this channel! You can't add more yet."
                )
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

    # @christmas.command(name="leaderboard")
    async def leaderboard(
        self, ctx, board: Literal["Staff", "User"], type: Literal["thrown", "hit"]
    ):
        if type == "thrown":
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetch(
                    f"""SELECT u_id, times_thrown FROM events_new WHERE times_thrown != 0 ORDER BY times_thrown DESC"""
                )
                exps = [t["times_thrown"] for t in details]
                ids = [record["u_id"] for record in details]
                embed = discord.Embed(
                    title="Snowballs Thrown Leaderboard",
                    description="Toss snowballs at players during our event to rise in these rankings!",
                    color=0xFFB6C1,
                )
                desc = ""
                true_idx = 1
                for idx, id in enumerate(ids):
                    # if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                    # continue
                    tnick, staff = await pconn.fetchrow(
                        "SELECT tnick, staff FROM users WHERE u_id = $1", id
                    )
                    exp = exps[idx]
                    if board == "Staff":
                        if id == 744831273406824449:
                            pass
                        elif staff not in ("Admin", "Mod", "Investigator"):
                            continue
                    elif board == "User":
                        if staff != "User" or id == 744831273406824449:
                            continue
                    else:
                        await ctx.send(
                            "That is not a valid event leaderboard type, please try again..."
                        )
                        return
                    if tnick is not None:
                        name = f"{tnick} - ({id})"
                    else:
                        name = f"Unknown user - ({id})"
                    desc += f"__{true_idx}__. `Position` : **{exp}** - `{name}`\n"
                    true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        elif type == "hit":
            async with ctx.bot.db[0].acquire() as pconn:
                details = await pconn.fetch(
                    f"""SELECT u_id, times_hit FROM events_new WHERE times_thrown != 0 ORDER BY times_hit DESC"""
                )
                exps = [t["times_hit"] for t in details]
                ids = [record["u_id"] for record in details]
                embed = discord.Embed(
                    title="Snowballs Hit Leaderboard",
                    description="Get hit by snowballs during our event to rise in these rankings!",
                    color=0xFFB6C1,
                )
                desc = ""
                true_idx = 1
                for idx, id in enumerate(ids):
                    # if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                    # continue
                    tnick, staff = await pconn.fetchrow(
                        "SELECT tnick, staff FROM users WHERE u_id = $1", id
                    )
                    exp = exps[idx]
                    if board == "Staff":
                        if id == 744831273406824449:
                            pass
                        elif staff not in ("Admin", "Mod", "Investigator"):
                            continue
                    elif board == "User":
                        if staff != "User" or id == 744831273406824449:
                            continue
                    else:
                        await ctx.send(
                            "That is not a valid event leaderboard type, please try again..."
                        )
                        return
                    if tnick is not None:
                        name = f"{tnick} - ({id})"
                    else:
                        name = f"Unknown user - ({id})"
                    desc += f"__{true_idx}__. `Position` : **{exp}** - `{name}`\n"
                    true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()

    # @christmas.command(name="snowball")
    async def throw_snowball(self, ctx, player: discord.Member):
        if ctx.guild != ctx.bot.official_server:
            await ctx.send(
                "You can only use this command in the Mewbot Official Server."
            )
            return
        if ctx.author.id == player.id:
            await ctx.send(
                "Santa does not like a cheater!\nThrow it at someone else..."
            )
            return
        async with ctx.bot.db[0].acquire() as pconn:
            msg = ""
            (
                snowballs,
                times_hit,
                times_thrown,
                trainer_redeemed,
                role_redeemed,
            ) = await pconn.fetchrow(
                "SELECT snowballs, times_hit, times_thrown, trainer_redeemed, role_redeemed FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
            if snowballs is None:
                await ctx.send("You have not started the event!")
                return
            elif snowballs < 1:
                await ctx.send(
                    "You have to get some snowballs <:snowballs:1184292806190182420>!"
                )
                return

            attacked_times_hit = await pconn.fetchval(
                "SELECT times_hit FROM events_new WHERE u_id = $1", player.id
            )
            if attacked_times_hit is None:
                # Meaning player hit hasn't started event
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    player.id,
                )
                await ctx.send("Please try this command again shortly...")
                return

            # Let's hit player
            await pconn.execute(
                "UPDATE events_new SET times_hit = times_hit + 1 WHERE u_id = $1",
                player.id,
            )
            # Remove snowball and update stats
            snowballs -= 1
            times_thrown += 1
            await pconn.execute(
                "UPDATE events_new SET snowballs = $1, times_thrown = $2 WHERE u_id = $3",
                snowballs,
                times_thrown,
                ctx.author.id,
            )
            if times_thrown >= 100 and role_redeemed is False:
                event_role = ctx.guild.get_role(1184182751067377674)
                await ctx.author.add_roles(
                    event_role, reason=f"Event threshold reward - {ctx.author}"
                )
                await pconn.execute(
                    "UPDATE events_new SET role_redeemed = True WHERE u_id = $1",
                    ctx.author.id,
                )
                msg += "You've received the Xmas2023 Official Server Role!"
            elif times_thrown >= 250 and trainer_redeemed is False:
                # TODO: For xmas2024 this needs to be updated with new trainer imgs
                choice = await ListSelectView(
                    ctx, "Please choose a trainer image!"
                ).wait()
                if choice is None:
                    await ctx.send("You did not select in time, cancelling.")
                    self.purchaselock.remove(ctx.author.id)
                    return
                trainer_images = await pconn.fetchval(
                    "SELECT trainer_images::json FROM account_bound WHERE u_id = $1",
                    ctx.author.id,
                )
                choice = str(choice)
                category = "xmas"
                if category not in trainer_images:
                    trainer_images[category] = {}
                if choice not in trainer_images[category]:
                    trainer_images[category][choice] = 1
                else:
                    trainer_images[category][choice] += 1
                await pconn.execute(
                    "UPDATE account_bound SET trainer_images = $1::json WHERE u_id = $2",
                    trainer_images,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET trainer_redeemed = True WHERE u_id = $1",
                    ctx.author.id,
                )
                msg += f"You've successfully redeemed {choice} as your trainer image!\nIt's been added to your trainer image inventory."

        embed = discord.Embed(
            title="Mewbot Christmas",
            description=f"You've throw a snowball!\nDid it hit?!",
            color=0x0084FD,
        )
        embed.add_field(
            name="Victim", value=f"You've hit **{player.name}**!", inline=False
        )
        embed.add_field(
            name=f"{ctx.author.name}'s Stats",
            value=f"You've been hit __{times_hit} times__.\nYou've thrown __{times_thrown} snowballs__!",
            inline=False,
        )
        if msg != "":
            embed.add_field(name="Rewards", value=f"{msg}", inline=False)
        await ctx.send(embed=embed)

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
                await ctx.send(
                    "There is already honey in this channel! You can't add more yet."
                )
                return
            if "holiday cheer" in inv and inv["holiday cheer"] >= 1:
                inv["holiday cheer"] -= 1
                pass
            else:
                await ctx.send(
                    "You do not have any holiday cheer, catch some pokemon to find some!"
                )
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
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def christmas_buy(
        self,
        ctx,
        pack: Literal[
            "1. 2x Battle Multi.",
            "2. 2x Shiny Multi.",
            "3. 1-25 Gleam Gems",
            "4. Event Gleam",
            "5. Boosted Event Gleam",
            "6. Returning Gleams",
            "7. Returning Radiants",
        ],
    ):
        """Buy something from the christmas shop."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Not available at the moment!")
        # return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        option = int(pack[0])
        if option < 1 or option > 7:
            await ctx.send("That is not a valid option number.")
            return
        if ctx.author.id in self.purchaselock:
            await ctx.send("Please finish any pending purchases!")
            return

        async with self.bot.db[0].acquire() as pconn:
            credits, redeems = await pconn.fetchrow(
                "SELECT mewcoins, redeems FROM users WHERE u_id = $1", ctx.author.id
            )
            if credits is None:
                await ctx.send(
                    "You haven't started! Please use `/start` to start your adventure!"
                )
                return

            radiant_gems, battle_multiplier, shiny_multiplier = await pconn.fetchrow(
                "SELECT radiant_gem, battle_multiplier, shiny_multiplier FROM account_bound WHERE u_id = $1",
                ctx.author.id,
            )
            if radiant_gems is None:
                await ctx.send(
                    "No bound items table found. Have you started or converted to the new bag system if needed?"
                )
                return

            gleam_limit, radiant_limit = await pconn.fetchrow(
                "SELECT gleam_limit, radiant_limit FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
            if gleam_limit is None:
                # Try to add user to table and then have them redo the command
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    ctx.author.id,
                )
                await ctx.send("Please retry the command.")
                return

            self.purchaselock.append(ctx.author.id)

            # Battle Multiplier
            if option == 1:
                if credits < 50000:
                    await ctx.send("You don't have enough credits for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if battle_multiplier >= 50:
                    await ctx.send("Your Battle Multiplier is already maxed out!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                battle_multiplier = min(battle_multiplier + 2, 50)
                await pconn.execute(
                    "UPDATE account_bound SET battle_multiplier = $1 WHERE u_id = $2",
                    battle_multiplier,
                    ctx.author.id,
                )
                await ctx.send("You have successfully purchased 2x Battle Multiplier!")
                self.purchaselock.remove(ctx.author.id)
                return

            # Shiny Multiplier
            if option == 2:
                if credits < 50000:
                    await ctx.send("You don't have enough snowflakes for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if shiny_multiplier >= 50:
                    await ctx.send("Your Shiny Multiplier is already maxed out!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                shiny_multiplier = min(shiny_multiplier + 2, 50)
                await pconn.execute(
                    "UPDATE account_bound SET shiny_multiplier = $1 WHERE u_id = $2",
                    shiny_multiplier,
                    ctx.author.id,
                )
                await ctx.send("You have successfully purchased 2x Shiny Multiplier!")
                self.purchaselock.remove(ctx.author.id)
                return

            # Gleam Gems
            if option == 3:
                if credits < 50000:
                    await ctx.send("You don't have enough credits for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                credits -= 50000
                earned_gleams = random.randint(1, 25)
                await pconn.execute(
                    "UPDATE users SET mewcoins = $1 WHERE u_id = $2",
                    credits,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = radiant_gem + $1 WHERE u_id = $2",
                    earned_gleams,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You bought {earned_gleams}x Gleam Gems <a:radiantgem:774866137472827432>."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Event Gleams
            # Gives the skin for the Pokemon rather than the Pokemon
            if option == 4:
                if radiant_gems < 150:
                    await ctx.send(
                        "You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!"
                    )
                    self.purchaselock.remove(ctx.author.id)
                    return
                radiant_gems -= 150
                skins = await pconn.fetchval(
                    "SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id
                )
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "xmas2023" not in skins[pokemon]:
                    skins[pokemon]["xmas2023"] = 1
                else:
                    skins[pokemon]["xmas2023"] += 1
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = $1 WHERE u_id = $2",
                    radiant_gems,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE users SET skins = $1::json WHERE u_id = $2",
                    skins,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You got a **{pokemon.title()} Christmas Skin**! Apply it with `/skin apply`."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Boosted Event Glems
            # This gives Pokemon w/skin rather than just skin
            if option == 5:
                if radiant_gems < 300:
                    await ctx.send(
                        "You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!"
                    )
                    self.purchaselock.remove(ctx.author.id)
                    return
                radiant_gems -= 300
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = $1 WHERE u_id = $2",
                    radiant_gems,
                    ctx.author.id,
                )
                await ctx.bot.commondb.create_poke(
                    ctx.bot,
                    ctx.author.id,
                    pokemon.capitalize(),
                    boosted=True,
                    skin="xmas2023",
                )
                await ctx.send(
                    f"You got a **{pokemon.title()} Christmas Pokemon**!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Returning Gleams
            if option == 6:
                if radiant_gems < 300:
                    await ctx.send(
                        "You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!"
                    )
                    self.purchaselock.remove(ctx.author.id)
                    return
                if gleam_limit >= 50:
                    await ctx.send("You have hit the purchase limit for the event!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                radiant_gems -= 300
                pokemon = random.choice(GLEAM_POKEMON).lower()
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = $1 WHERE u_id = $2",
                    radiant_gems,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET gleam_limit = gleam_limit + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon.capitalize(), skin="gleam"
                )
                await ctx.send(
                    f"You got a **<:gleam:1010559151472115772> {pokemon.title()} **!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            # Returning Radiants
            if option == 7:
                if redeems < 200:
                    await ctx.send("You don't have enough Redeems for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                if radiant_limit >= 20:
                    await ctx.send("You have hit the purchase limit for the event!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                redeems -= 200
                pokemon = random.choice(RADIANT_POKEMON).lower()
                await pconn.execute(
                    "UPDATE users SET redeems = $1 WHERE u_id = $2",
                    redeems,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET radiant_limit = radiant_limit + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon.capitalize(), skin="radiant"
                )
                await ctx.send(
                    f"You got a **<:radiant:1010558960027308052> {pokemon.title()} **!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

    # @christmas.command(name="inventory")
    async def christmas_inventory(self, ctx):
        """Check your christmas inventory."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Not available at the moment!")
        # return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchrow(
                "SELECT snowflakes, small_gift, large_gift, snowballs, times_hit, times_thrown FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
        embed = discord.Embed(
            title=f"{ctx.author.name.title()}'s Christmas Inventory",
            description=f"These are all items that are related to the event.\nGet all of these items from RAIDS!",
            color=random.choice(RED_GREEN),
        )
        embed.add_field(
            name="Snowballs <:snowballs:1184292806190182420>",
            value=f"**Available**: {inventory['snowballs']}x\n**Times Hit**: {inventory['times_hit']}\n**Times Thrown**: {inventory['times_thrown']}",
            inline=False,
        )
        embed.add_field(
            name="Presents",
            value=(
                f"**Small Present** 📦: {inventory['small_gift']}x\n"
                f"**Large Present** 🎁: {inventory['large_gift']}x"
            ),
            inline=False,
        )
        # if "holiday cheer" in inventory:
        # embed.add_field(name="Holiday Cheer",
        # value=f"{inventory['holiday cheer']}x")
        embed.set_footer(text="Happy Holidays!")
        await ctx.send(embed=embed)

    # @christmas.command(name="shop")
    async def christmas_shop(self, ctx):
        """Check the christmas shop."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Not available at the moment!")
        # return

        event_data = await ctx.bot.db[0].fetchrow(
            "SELECT radiant_limit, gleam_limit FROM events_new WHERE u_id = $1",
            ctx.author.id,
        )
        if event_data is None:
            radiant_limit = 0
            gleam_limit = 0
        else:
            radiant_limit = event_data["radiant_limit"]
            gleam_limit = event_data["gleam_limit"]

        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return

        embed = discord.Embed(
            title="Christmas Shop",
            description="Make sure to join RAIDS to maximize your income during the event!\nJoin our Official Server and grab the role! `/invite`",
            color=random.choice(RED_GREEN),
        )
        embed.add_field(
            name="Account Multipliers",
            value=(
                "`1.` __2x Battle Multi.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
                "`2.` __2x Shiny Multi.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Currencies",
            value=(
                "`3.` __1-25 Gleam Gems.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Gleams",
            value=(
                "`4.` __Event Skin__\n**Cost:** 150 <a:radiantgem:774866137472827432>\nThis is a skin that goes into inventory!\n"
                "`5.` __Boosted Event Skin__\n**Cost:** 300 <a:radiantgem:774866137472827432>\nThis is a Pokemon already with the skin equipped!"
            ),
            inline=False,
        )
        embed.add_field(
            name="Returning Gleams",
            value=(
                "`6.` __Returning Gleams__\n"
                "**Cost:** 300 <a:radiantgem:774866137472827432>\n"
                f"Purchase Limit: {gleam_limit} / 50\nGleams from 2023."
            ),
            inline=False,
        )
        embed.add_field(
            name="Returning Radiants",
            value=(
                "`7.` __Returning Radiants__\n"
                "**Cost:** 200 <:redeem:1037942226132668417>\n"
                f"Purchase Limit: {radiant_limit} / 20\n"
                ""
            ),
            inline=False,
        )
        embed.set_footer(text="Use /christmas buy to buy an item!")
        await ctx.send(embed=embed)

    # @christmas.command(name="smallgift")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def open_smallgift(self, ctx):
        """Open a small christmas gift."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Sorry, this is not available yet")
        # return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            small_gift = await pconn.fetchval(
                "SELECT small_gift FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if small_gift is None:
                await ctx.send(
                    f"You have not Started or participated in the event yet!\nStart with `/start` first!"
                )
                return
            if small_gift <= 0:
                await ctx.send("You do not have any small gifts!")
                return
            small_gift -= 1
            await pconn.execute(
                "UPDATE events_new SET small_gift = $1 where u_id = $2",
                small_gift,
                ctx.author.id,
            )
        reward = random.choices(
            ("normalice", "shinyice", "snowballs", "radiant_gems", "energy"),
            weights=(0.10, 0.15, 0.35, 0.20, 0.20),
        )[0]

        if reward == "normalice":
            pool = pList + starterList
            pokemon = random.choice(pool)
            await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon)
            msg = f"Upon opening the gift...\nYou received a **{pokemon}**!"

        elif reward == "shinyice":
            pool = pList + starterList
            pokemon = random.choice(pool)
            await ctx.bot.commondb.create_poke(
                ctx.bot, ctx.author.id, pokemon, shiny=True
            )
            msg = f"Upon opening the gift...\nYou received a **Shiny {pokemon}**!"

        elif reward == "snowballs":
            async with ctx.bot.db[0].acquire() as pconn:
                snowballs = random.randint(1, 5)
                await pconn.execute(
                    "UPDATE events_new SET snowballs = snowballs + $1 WHERE u_id = $2",
                    snowballs,
                    ctx.author.id,
                )
            msg = f"You opened the gift, and inside was {snowballs} <:snowballs:1184292806190182420> Snowballs !"

        elif reward == "radiant_gems":
            amount = random.randint(1, 5)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = radiant_gem + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You opened the gift, and inside was {amount} Gleam Gems!"

        elif reward == "energy":
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET npc_energy = npc_energy + 2 WHERE u_id = $1",
                    ctx.author.id,
                )
            msg = "You stole some of Santa's cookies and milk! It restored some npc energy!\n"
        await ctx.send(msg)

    # @christmas.command(name="largegift")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def open_largegift(self, ctx):
        """Open a large christmas gift."""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Sorry, this is not available yet")
        # return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            large_gift = await pconn.fetchval(
                "SELECT large_gift FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if large_gift is None:
                await ctx.send(
                    f"You have not Started or participated in the event yet!\nStart with `/start` first!"
                )
                return
            if large_gift <= 0:
                await ctx.send("You do not have any large gifts!")
                return
            large_gift -= 1
            await pconn.execute(
                "UPDATE events_new SET large_gift = $1 where u_id = $2",
                large_gift,
                ctx.author.id,
            )
        reward = random.choices(
            ("radiant_gems", "credits", "chest", "boostedice", "shinyice"),
            weights=(0.20, 0.35, 0.15, 0.20, 0.10),
        )[0]

        if reward == "radiant_gems":
            amount = random.randint(1, 10)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = radiant_gem + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received **{amount} Gleam Gems**!"

        elif reward == "credits":
            amount = random.randint(5000, 10000)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"Upon opening the gift...\nYou received **{amount:,} credits**!"

        elif reward == "chest":
            chest = random.choices(
                ("common_chest", "rare_chest", "mythic_chest"),
                weights=(0.60, 0.20, 0.10),
            )[0]
            await ctx.bot.commondb.add_bag_item(ctx.author.id, chest, 1, True)
            chest_name = chest.replace("_", " ").title()
            msg = f"Upon opening the gift...\nYou received a **{chest_name}**!"

        elif reward == "boostedice":
            pool = pList + starterList
            pokemon = random.choice(pool)
            await ctx.bot.commondb.create_poke(
                ctx.bot, ctx.author.id, pokemon, boosted=True
            )
            msg = f"Upon opening the gift...\nYou received a **Boosted IV {pokemon}**!"

        elif reward == "shinyice":
            pool = pList + starterList
            pokemon = random.choice(pool)
            await ctx.bot.commondb.create_poke(
                ctx.bot, ctx.author.id, pokemon, boosted=True, shiny=True
            )
            msg = f"Upon opening the gift...\nYou received a **Shiny Boosted IV {pokemon}**!"

        # Large Gift gives snowballs
        snowballs = random.randint(1, 2)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE events_new SET snowballs = snowballs + $1 WHERE u_id = $2",
                snowballs,
                ctx.author.id,
            )
        msg += f"\nThere was also {snowballs} <:snowballs:1184292806190182420> Snowballs!\nUse `/christmas snowball` to throw it at a player!"
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
            if await pconn.fetchval(
                "SELECT tradelock FROM users WHERE u_id = $1", ctx.author.id
            ):
                await ctx.send("You are tradelocked, sorry")
                return
            curcreds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
            )
        if curcreds is None:
            await ctx.send(
                f"{ctx.author.name} has not started... Start with `/start` first!"
            )
            return
        if amount > curcreds:
            await ctx.send("You don't have that many credits!")
            return
        if not await ConfirmView(
            ctx,
            f"Are you sure you want to donate {amount}<:mewcoin:1010959258638094386> to the christmas raffle prize pool?",
        ).wait():
            await ctx.send("Canceled")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            curcreds = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
            )
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
                ctx.author.id,
                920827966928326686,
                amount,
                "xmasgift",
                datetime.now(),
            )

    # @commands.hybrid_group()
    async def unown(self, ctx):
        """Unown commands"""
        pass

    # @unown.command(name="guess")
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
            letters = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id
            )
        if letters is None:
            await ctx.send("You have not started yet.\nStart with `/start` first!")
            return
        if letters.get(letter, 0) <= 0:
            await ctx.send(f"You don't have any {self.UNOWN_CHARACTERS[1][letter]}s!")
            return
        letters[letter] -= 1
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET holidayinv = $2::json WHERE u_id = $1",
                ctx.author.id,
                letters,
            )
        for idx, character in enumerate(self.UNOWN_WORD):
            if character == letter and self.UNOWN_GUESSES[idx] is None:
                self.UNOWN_GUESSES[idx] = ctx.author.id
                break
        else:
            await ctx.send("That letter isn't in the word!")
            return
        # Successful guess
        await ctx.send(
            "Correct! Added your letter to the board. You will be rewarded if the word is guessed."
        )
        await self.update_unown()

    # @unown.command(name="inventory")
    async def unown_inventory(self, ctx):
        """Check your unown inventory"""
        async with ctx.bot.db[0].acquire() as pconn:
            letters = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", ctx.author.id
            )
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

    # @unown.command(name="start")
    # @check_mod()
    async def unown_start(self, ctx, channel: discord.TextChannel, word: str):
        """Start the unown game"""
        if not await check_mod().predicate(ctx):
            await ctx.send("This command is only available to staff.")
            return
        if self.UNOWN_WORD:
            await ctx.send("There is already an active unown event!")
            return
        word = word.lower()
        if "".join(c for c in word if c in "abcdefghijklmnopqrstuvwxyz ") != word:
            await ctx.send("Word can only contain a-z and spaces!")
            return
        self.UNOWN_WORD = word
        self.UNOWN_GUESSES = [145519400223506432 if l == " " else None for l in word]
        self.UNOWN_MESSAGE = await channel.send(
            embed=discord.Embed(description="Setting up...")
        )
        await self.update_unown()
        await ctx.send("Event started!")

    async def give_balloons(self, channel, user):
        """Gives some balloons to the provided user."""
        carrots = random.randint(1, 3)
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id,
            )
            await pconn.execute(
                f"UPDATE events_new SET snowballs = snowballs + $1 WHERE u_id = $2",
                carrots,
                user.id,
            )
            embed = discord.Embed(
                title="Summer Event!",
                description=f"The Pokemon was holding {carrots}x <:waterballoon:1273431369749495930>s!\nUse command `/summer wb` to use them!",
                color=0x0084FD,
            )
        await channel.send(embed=embed)

    async def give_egg(self, channel, user):
        """Gives some carrots to the provided user."""
        carrots = random.randint(5, 10)
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id,
            )
            await pconn.execute(
                f"UPDATE events_new SET carrots = carrots + $1 WHERE u_id = $2",
                carrots,
                user.id,
            )
            embed = discord.Embed(
                title="Easter Event!",
                description=f"The Pokemon was holding {carrots}x 🥕s!\nUse command `/easter shop` to use them!",
                color=ORANGE,
            )
        await channel.send(embed=embed)

    async def give_candy(self, ctx, amount=0):
        """Gives candy to the provided user."""
        if type(ctx) == list:
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    ctx[1].id,
                )
                await pconn.execute(
                    "UPDATE events_new SET candy = candy + $1 WHERE u_id = $2",
                    amount if amount else random.randint(1, 3),
                    ctx[1].id,
                )
            await ctx[0].send(
                embed=make_embed(
                    title=f"Dropped some candy!\nUse command `/halloween inventory` to view what you have collected."
                )
            )
            return

        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE events_new SET candy = candy + $1 WHERE u_id = $2",
                amount if amount else random.randint(1, 3),
                ctx.author.id,
            )
        await ctx.send(
            embed=make_embed(
                title=f"Dropped some candy!\nUse command `/halloween inventory` to view what you have collected."
            )
        )

    async def drop_potions(self, ctx, amount=0):
        """Drops potions to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                ctx.author.id,
            )
            await pconn.execute(
                "UPDATE events_new SET potion = potion + $1 WHERE u_id = $2",
                amount if amount else random.randint(1, 3),
                ctx.author.id,
            )
        await ctx.send(
            embed=make_embed(
                title=f"Dropped some potions!\nUse command `/halloween inventory` to view what you have collected."
            )
        )

    async def give_bone(self, channel, user):
        """Gives potions to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO halloween (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id,
            )
            await pconn.execute(
                "UPDATE halloween SET bone = bone + $1 WHERE u_id = $2",
                random.randint(1, 3),
                user.id,
            )
        await channel.send(
            f"The pokemon dropped some potions!\nUse command `/halloween inventory` to view what you have collected."
        )

    def rand_pumpkin_title(self):
        return random.choice(
            [
                "🎃 A wild pumpkin has appeared! Grab it before it disappears!",
                "Look! A spooky pumpkin awaits... Will you bag it for later?",
                "👻 A mysterious pumpkin appears in the shadows... Bag it now or miss out!",
            ]
        )

    def rand_bag_text(self):
        return random.choice(
            [
                "You bagged the pumpkin! 🎃 Wonder what’s inside…",
                "The pumpkin is safely stowed away for later. Who knows what awaits inside?",
                "🎃 Pumpkin bagged! You can open it when you’re ready for a treat... or trick!",
            ]
        )

    async def spawn_pumpkin(self, channel, user):
        # Possible rewards and trick message
        PUMPKIN_REWARDS = [
            "a Rare Candy 🍬",
            "a Ghost-type Pokémon encounter 👻",
            "some Stardust ✨",
            "a Mystery Box 🎁",
        ]
        TRICK_MESSAGE = "👻 You've been tricked! Better luck next time."
        # Create a random position for the "correct" button
        correct_button_index = random.randint(0, 8)

        # Embed message for the pumpkin challenge
        e = discord.Embed(
            title=self.rand_pumpkin_title(),
            description="Press the right button quick! You only have a couple seconds to receive a massive treat!",
            color=discord.Color.orange(),
        )
        e.set_image(
            url="https://mewbot.xyz/img/pumpkin.jpg"
        )  # Replace with Halloween image URL

        view = discord.ui.View(timeout=5)

        # Callback function for each button
        async def button_callback(interaction: discord.Interaction, index: int):
            if index == correct_button_index:
                reward = random.choice(PUMPKIN_REWARDS)
                e.title = "🎉 You found the treat!"
                e.description = self.rand_bag_text()
                await self.give_pumpkin(interaction.user, 1)
                await interaction.response.edit_message(embed=e, view=None)
            else:
                e.title = "🎃 Wrong button!"
                e.description = TRICK_MESSAGE
                await interaction.response.edit_message(embed=e, view=None)

        # Add buttons to the view
        for i in range(9):
            # Use 🎃 or 👻 emoji for each button
            button = discord.ui.Button(
                label="",
                emoji="🎃" if i % 2 == 0 else "👻",
                style=(
                    discord.ButtonStyle.secondary
                    if i % 2 == 0
                    else discord.ButtonStyle.primary
                ),
            )
            button.callback = lambda interaction, idx=i: button_callback(
                interaction, idx
            )
            view.add_item(button)
            # Send the initial message with pumpkin challenge
        msg = await channel.send(embed=e, view=view)

        try:
            interaction: discord.Interaction = await self.bot.wait_for(
                "button_click", check=lambda i: i.message.id == msg.id, timeout=120
            )
        except:
            e.title = "🎃 Time's up!"
            e.description = TRICK_MESSAGE
            await msg.edit(embed=e, view=None)

    async def give_pumpkin(self, user, amount):
        """Gives pumpkins to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id,
            )
            await pconn.execute(
                "UPDATE events_new SET pumpkin = pumpkin + $1 WHERE u_id = $2",
                amount,
                user.id,
            )

    async def get_ghosts(self):
        data = await self.bot.db[1].ptypes.find({"types": 8}).to_list(None)
        data = [x["id"] for x in data]
        data = (
            await self.bot.db[1].forms.find({"pokemon_id": {"$in": data}}).to_list(None)
        )
        data = [x["identifier"].title() for x in data]
        return list(set(data) & set(totalList))

    async def get_ice(self):
        data = await self.bot.db[1].ptypes.find({"types": 15}).to_list(None)
        data = [x["id"] for x in data]
        data = (
            await self.bot.db[1].forms.find({"pokemon_id": {"$in": data}}).to_list(None)
        )
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
        await channel.send(
            f"The pokemon dropped some holiday cheer!\nUse command `/spread cheer` to share it with the rest of the server."
        )

    async def maybe_spawn_christmas(self, channel):
        # async with self.bot.db[0].acquire() as pconn:
        # honey = await pconn.fetchval(
        # "SELECT type FROM honey WHERE channel = $1 LIMIT 1",
        # channel.id,
        # )
        # if honey != "cheer":
        # return
        # await asyncio.sleep(random.randint(30, 45))
        await ChristmasSpawn(
            self, channel, "Lopunny"
        ).start()  # random.choice(self.EVENT_POKEMON)).start()

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
                check=lambda m: m.channel == channel
                and m.content.lower()
                .replace(f"<@{self.bot.user.id}>", "")
                .replace(" ", "", 1)
                == word,
                timeout=60,
            )
        except asyncio.TimeoutError:
            await message.delete()
            return

        async with self.bot.db[0].acquire() as pconn:
            letters = await pconn.fetchval(
                "SELECT holidayinv::json FROM users WHERE u_id = $1", winner.author.id
            )
            if letters is not None:
                letters[letter] = letters.get(letter, 0) + 1
                await pconn.execute(
                    "UPDATE users SET holidayinv = $2::json WHERE u_id = $1",
                    winner.author.id,
                    letters,
                )

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
                    winners[self.UNOWN_GUESSES[idx]] += self.UNOWN_POINTS[character]
            async with self.bot.db[0].acquire() as pconn:
                for uid, points in winners.items():
                    if points > 10:
                        points //= 10
                        inventory = await pconn.fetchval(
                            "SELECT inventory::json FROM users WHERE u_id = $1", uid
                        )
                        inventory["rare chest"] = (
                            inventory.get("rare chest", 0) + points
                        )
                        await pconn.execute(
                            "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                            inventory,
                            uid,
                        )
                        points = 10
                    await pconn.execute(
                        "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                        points * 5000,
                        uid,
                    )
                await pconn.execute("UPDATE users SET holidayinv = '{}'")
            embed = discord.Embed(
                title="You identified the word!",
                description=(
                    f"{formatted}\n\n"
                    "Users who guessed a letter correctly have been given credits.\n"
                ),
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
            ),
        )
        await self.UNOWN_MESSAGE.edit(embed=embed)

    @commands.Cog.listener()
    async def on_poke_spawn(self, channel, user):
        # For limiting raids to Official only
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS:
            if not random.randrange(10):
                await self.give_egg(channel, user)
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
        if self.HALLOWEEN_DROPS:

            func: Coroutine = random.choices(
                (self.give_candy, self.maybe_spawn_christmas), weights=(0.40, 0.60)
            )[0]

            try:
                await func([channel, user])
            except:
                await func(channel)

        if self.CHRISTMAS_DROPS:
            # if not random.randrange(15) or user.id == 334155028170407949:
            # await self.give_cheer(channel, user)
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
        if self.VALENTINE_DROPS:
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
        if self.SUMMER_DROPS:
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.give_balloons(channel, user)
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)

        # Dumb unown event stuff
        # if not random.randrange(10):
        # await self.maybe_spawn_unown(channel)

    @commands.Cog.listener()
    async def on_poke_fish(self, channel, user):
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS and not random.randrange(5):
            await self.give_egg(channel, user)
        if self.SUMMER_DROPS:
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.give_balloons(channel, user)
        if self.HALLOWEEN_DROPS:
            func: Coroutine = random.choices(
                (self.give_candy, self.spawn_pumpkin), weights=(0.60, 0.40)
            )[0]
            try:
                await func(channel, user)
            except:
                await func([channel, user])
        if not random.randrange(5):
            await self.maybe_spawn_unown(channel)

    @commands.Cog.listener()
    async def on_poke_breed(self, channel, user):
        if self.bot.botbanned(user.id):
            return
        if self.EASTER_DROPS:
            if not random.randrange(10):
                await self.give_egg(channel, user)
        if self.SUMMER_DROPS:
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.give_balloons(channel, user)
        if self.HALLOWEEN_DROPS:
            func: Coroutine = random.choices(
                (self.give_candy, self.spawn_pumpkin), weights=(0.60, 0.40)
            )[0]

            try:
                await func(channel, user)
            except:
                await func([channel, user])
        # if not random.randrange(7):
        # await self.maybe_spawn_unown(channel)


class ChristmasSpawn(discord.ui.View):
    """A spawn embed for a christmas spawn."""

    def __init__(self, cog, channel, poke: str):
        super().__init__(timeout=140)
        self.cog = cog
        self.channel = channel
        self.poke = poke
        self.servercache = []
        self.registered = []
        self.attacked = {}
        self.max_hp = 100
        self.hp = 100
        self.state = "registering"
        self.timeout = 120
        self.message: discord.Message = None
        self.DUELAPI_URL = "http://178.28.0.11:5864/healthbar"
        self.banned = [
            1075429458271547523,
        ]

    async def interaction_check(self, interaction):
        if self.state == "registering":
            if interaction.user in self.registered:
                await interaction.response.send_message(
                    content="You have already joined!\nWait for the others!",
                    ephemeral=True,
                )
                return False
            return True
        elif self.state == "attacking":
            # if interaction.user in self.attacked:
            #     await interaction.response.send_message(
            #         content="You have already attacked!", ephemeral=True
            #     )
            #     return True
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

    def rand_spawn_title(self):
        return random.choice(
            [
                f"🎄 A festive breeze carries a wild {self.poke} your way!",
                f"🎅 Under the twinkling Christmas lights, a jolly {self.poke} has appeared!",
                f"✨ A magical glow surrounds {self.poke} as it steps out of a winter wonderland!",
                f"❄️ Amidst the falling snow, you spot a holiday {self.poke} looking for cheer!",
                f"🎁 The spirit of Christmas is here, and {self.poke} has come to celebrate!",
            ]
        )

    def pokemon_escaped_message(self):
        return random.choice(
            [
                f"🎄 The wild {self.poke} was feeling too jolly and danced away into the snow!",
                f"🎅 {self.poke} vanished with a ho-ho-ho! Better luck next time!",
                f"✨ {self.poke} slipped away under the cover of twinkling Christmas lights!",
                f"❄️ A gust of winter wind carried {self.poke} far away. It’s gone for now!",
                f"🎁 {self.poke} decided to deliver presents elsewhere. Keep an eye out for another chance!",
            ]
        )
    
    def rand_defeat_message(self):
        return random.choice(
            [
                f"❄️ {self.poke} fades into the snow, leaving behind a chilling silence...",
                f"🎄 The festive lights dim as {self.poke} retreats into the winter night.",
                f"🎁 {self.poke} leaves behind a parting gift of snowflakes as it vanishes!",
                f"✨ {self.poke} sparkles one last time before disappearing into the frosty ether.",
                f"🎅 With a jolly nod, {self.poke} bids farewell and vanishes into the holiday mist!",
                f"❄️ The snow settles as {self.poke} is no longer in sight.",
                f"🎁 {self.poke} leaves with a parting twinkle, disappearing into the magic of the season.",
                f"🎄 The jingling bells quiet as {self.poke} drifts away into the winter wonderland.",
                f"✨ The glow around {self.poke} fades, leaving only a frosty memory behind.",
                f"🎅 With a merry wave, {self.poke} departs, its holiday spirit lingering in the air!",
            ]
        )


    async def stream_image(self):
        params = {
            "poke_image_url": "sprites/"
            + await get_file_name(self.poke, self.cog.bot, skin="xmas2024"),
            "poke": ujson.dumps({"hp": self.hp, "starting_hp": self.max_hp}),
        }
        image = BytesIO()
        async with aiohttp.ClientSession() as session:
            async with session.post(self.DUELAPI_URL, params=params) as resp:
                image.write(await resp.read())
        image.seek(0)
        file = discord.File(image, "event.png")
        return file
    
    def pick_winners(self):
        # Separate participants into high and low damage tiers
        sorted_participants = sorted(
            self.attacked.items(), key=lambda x: x[1], reverse=True
        )
        half_count = max(1, len(sorted_participants) // 2)

        # Randomly pick from the top 75% damage dealers
        top_damage_dealers = sorted_participants[: int(len(sorted_participants) * 0.75)]
        low_damage_dealers = sorted_participants[int(len(sorted_participants) * 0.75):]

        # Select winners
        top_picks = random.sample(top_damage_dealers, min(len(top_damage_dealers), half_count - len(low_damage_dealers)))
        low_picks = random.sample(low_damage_dealers, min(len(low_damage_dealers), len(top_damage_dealers) // 4))

        winners = top_picks + low_picks
        random.shuffle(winners)  # Shuffle to make it more fun!
        return winners

    async def start(self):
        # This should stop from more than one raid appearing
        # in any server that's not Official
        if self.channel.guild.id in self.servercache:
            return
        else:
            if self.channel.guild.id != 998128574898896906:
                self.servercache.append(self.channel.guild.id)

        extra_msg = ""
        pokeurl = "http://mewbot.xyz/sprites/" + await get_file_name(
            self.poke, self.cog.bot, skin="xmas2024"
        )
        guild = await self.cog.bot.mongo_find("guilds", {"id": self.channel.guild.id})
        if guild is None:
            small_images = False
        else:
            small_images = guild["small_images"]
        self.embed = discord.Embed(
            title=self.rand_spawn_title(),
            description="Join the battle to take it down.\nDo more damage to increase your chances of getting this raid Pokemon!!",
            color=0x0084FD,
        )
        self.embed.add_field(name="Take Action", value="Click the Button to join!")
        if small_images:
            self.embed.set_thumbnail(url=pokeurl)
        else:
            self.embed.set_image(url=pokeurl)
        self.add_item(RaidJoin())

        # Checks if message is in Official to use Raid Ping
        if self.channel.guild.id == 998128574898896906:
            am = discord.AllowedMentions.none()
            am.roles = True
            ping = "<@&998320324477190184>"
            self.message = await self.channel.send(
                ping, embed=self.embed, view=self, allowed_mentions=am
            )
        else:
            self.message = await self.channel.send(embed=self.embed, view=self)

        await asyncio.sleep(20)
        self.clear_items()

        if not self.registered:
            embed = discord.Embed(
                title=self.pokemon_escaped_message(),
                color=0x0084FD,
            )
            if small_images:
                embed.set_thumbnail(url=pokeurl)
            else:
                embed.set_image(url=pokeurl)
            await self.message.edit(embed=embed, view=None)
            return

        # Old system that uses CHRISTAS MOVES above
        # moves = []
        # for idx, move in enumerate(self.cog.CHRISTMAS_MOVES[self.poke]):
        # damage = max(2 - idx, 0)
        # moves.append(RaidMove(move, damage))
        # random.shuffle(moves)
        # for move in moves:
        # self.add_item(move)

        # New move system from skins
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
                {
                    "type_id": {"$in": super_types},
                    "damage_class_id": {"$ne": 1},
                    "id": {"$nin": uncoded_ids},
                }
            )
            .to_list(None)
        )
        super_moves = [
            x["identifier"].capitalize().replace("-", " ") for x in super_raw
        ]
        normal_raw = (
            await self.cog.bot.db[1]
            .moves.find(
                {
                    "type_id": {"$in": normal_types},
                    "damage_class_id": {"$ne": 1},
                    "id": {"$nin": uncoded_ids},
                }
            )
            .to_list(None)
        )
        normal_moves = [
            x["identifier"].capitalize().replace("-", " ") for x in normal_raw
        ]
        un_raw = (
            await self.cog.bot.db[1]
            .moves.find(
                {
                    "type_id": {"$in": un_types},
                    "damage_class_id": {"$ne": 1},
                    "id": {"$nin": uncoded_ids},
                }
            )
            .to_list(None)
        )
        un_moves = [x["identifier"].capitalize().replace("-", " ") for x in un_raw]

        # Add the moves to the view
        # The commented out code below adds type emojis to the buttons
        # Asked to be removed by GOMO during Halloween event
        # At least to start
        moves = []
        for i in range(4):
            if i == 0:
                move_name = random.choice(super_moves)
                # If you don't want type emotes, uncomment below
                # and comment out what's below it
                # moves.append(RaidMoveNoEmote(move_name, 2))

                type_id = await self.cog.bot.db[1].moves.find_one(
                    {"identifier": move_name.replace(" ", "-").lower()}
                )
                type_emoji = self.cog.bot.misc.get_type_emote(
                    (
                        await self.cog.bot.db[1].types.find_one(
                            {"id": type_id["type_id"]}
                        )
                    )["identifier"]
                )
                moves.append(RaidMove(move_name, 2, type_emoji))

            if i == 1:
                move_name = random.choice(normal_moves)
                # moves.append(RaidMoveNoEmote(move_name, 1))

                type_id = await self.cog.bot.db[1].moves.find_one(
                    {"identifier": move_name.replace(" ", "-").lower()}
                )
                type_emoji = self.cog.bot.misc.get_type_emote(
                    (
                        await self.cog.bot.db[1].types.find_one(
                            {"id": type_id["type_id"]}
                        )
                    )["identifier"]
                )
                moves.append(RaidMove(move_name, 1, type_emoji))

            elif i == 2:
                move_name = random.choice(un_moves)
                # moves.append(RaidMoveNoEmote(move_name, 0))

                type_id = await self.cog.bot.db[1].moves.find_one(
                    {"identifier": move_name.replace(" ", "-").lower()}
                )
                type_emoji = self.cog.bot.misc.get_type_emote(
                    (
                        await self.cog.bot.db[1].types.find_one(
                            {"id": type_id["type_id"]}
                        )
                    )["identifier"]
                )
                moves.append(RaidMove(move_name, 0, type_emoji))

            elif i == 3:
                move_name = random.choice(un_moves)
                # moves.append(RaidMoveNoEmote(move_name, 0))

                type_id = await self.cog.bot.db[1].moves.find_one(
                    {"identifier": move_name.replace(" ", "-").lower()}
                )
                type_emoji = self.cog.bot.misc.get_type_emote(
                    (
                        await self.cog.bot.db[1].types.find_one(
                            {"id": type_id["type_id"]}
                        )
                    )["identifier"]
                )
                moves.append(RaidMove(move_name, 0, type_emoji))
            else:
                pass

        random.shuffle(moves)
        for move in moves:
            self.add_item(move)

        self.max_hp = self.hp = int(len(self.registered) * self.max_hp * 1.25)
        self.embed = discord.Embed(
            title=self.rand_spawn_title(),
            description="Attack it with everything you've got!",
            color=0x0084FD,
        )
        self.embed.set_image(url="attachment://event.png")
        # self.embed.add_field(name="-", value=f"HP = {self.max_hp}/{self.max_hp}")
        # if small_images:
        #     self.embed.set_thumbnail(url=pokeurl)
        # else:
        #     self.embed.set_image(url=pokeurl)

        ## begin attack
        self.state = "attacking"
        await self.message.edit(
            embed=self.embed, attachments=[await self.stream_image()], view=self
        )

        while self.hp > 0:
            await asyncio.sleep(3)
            # hp = max(self.max_hp - sum(self.attacked.values()), 0)
            # self.embed.clear_fields()
            # self.embed.add_field(name="-", value=f"HP = {hp}/{self.max_hp}")/
            self.embed.set_image(url="attachment://event.png")
            await self.message.edit(embed=self.embed, attachments=[await self.stream_image()], view=self)
            await asyncio.sleep(3)

        self.state = "ended"
        # hp = max(self.max_hp - sum(self.attacked.values()), 0)
        if self.hp > 0:
            self.embed = discord.Embed(
                title="The Pokémon slipped and got away!🧟👻",
                description="Catch more Pokémon to spawn another one.",
                color=0x0084FD,
            )
            # hp = max(self.max_hp - sum(self.attacked.values()), 0)
            # self.embed.add_field(name="Status", value=f"HP = {hp}/{self.max_hp}")
            if small_images:
                self.embed.set_thumbnail(url=pokeurl)
            else:
                self.embed.set_image(url=pokeurl)
            await self.message.edit(embed=self.embed, view=None)
            return

        # Remove server from lock
        if self.channel.guild.id != 998128574898896906:
            self.servercache.remove(self.channel.guild.id)

        async with self.cog.bot.db[0].acquire() as pconn:
            winners = self.pick_winners()
            for winner in winners:
                await self.cog.bot.commondb.create_poke(self.cog.bot, winner, poke, skin = 'xmas2024')

        self.embed = discord.Embed(
            title=self.rand_defeat_message(),
            color=0x0084FD,
        )
        winner_mentions = ", ".join([f"<@{user_id}>" for user_id, _ in winners])
        self.embed.description += f"🎉 Congratulations to the winners of {self.pokemon_name}:\n{winner_mentions}!\nThank you for participating!"
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


# Has the Type Emote on Button
class RaidMove(discord.ui.Button):
    """A move button for attacking a christmas pokemon."""

    def __init__(self, move, damage, emote):
        super().__init__(label=move, emoji=emote, style=discord.ButtonStyle.gray)
        self.move = move
        self.damage = damage
        self.emote = emote

        if damage == 2:
            # "It's super effective! You will get a Large Present if the poke is defeated."
            # "It's super effective! You'll receive hearts if the poke is defeated!"
            # self.effective = (

            #     f"It's **Super Effective**!\nYou will get 9 to 15 seashells 🐚 if the Pokémon is defeated."
            # )
            self.effective = "It's Super Effective! You will get 10 :candy: if the Pokemon is defeated."

        elif damage == 1:
            # "It's not very effective... You will get a Small Present if the poke is defeated."
            # "It's not very effective... You'll receive hearts if the poke is defeated!"
            # self.effective = (
            #     f"It's **Not Very Effective**...\nYou will get 2 to 8 seashells 🐚 if the Pokémon is defeated."
            # )
            self.effective = "It's not Very Effective... You will get 5 :candy: if the Pokemon is defeated."

        else:
            # "It had no effect... You will only get Snowflakes if the poke is defeated."
            # "It had no effect... You'll receive hearts if the poke is defeated!"
            # self.effective = (
            #     f"It **Had No Effect**...\nYou will get 1 seashell 🐚 if the Pokémon is defeated."
            # )
            self.effective = (
                "It had No Effect... You will get a :candy: if the Pokemon is defeated."
            )

    async def callback(self, interaction):
        self.view.attacked[interaction.user] = (
            self.view.attacked.get(interaction.user, 0) + self.damage
        )
        self.view.hp -= self.damage
        await interaction.response.send_message(
            content=f"You used {self.move}. {self.effective}", ephemeral=True, delete_after = 2.00
        )


# No type emote on button
class RaidMoveNoEmote(discord.ui.Button):
    """A move button for attacking a christmas pokemon."""

    def __init__(self, move, damage):
        super().__init__(label=move, style=discord.ButtonStyle.gray)
        self.move = move
        self.damage = damage

        if damage == 2:
            # self.effective = "It's super effective! You will get a Large Present if the poke is defeated."
            # self.effective = "It's super effective! You'll receive hearts if the poke is defeated!"
            self.effective = "It's Super Effective! You will get a Fleshy Chest if the Pokemon is defeated."
        elif damage == 1:
            # self.effective = "It's not very effective... You will get a Small Present if the poke is defeated."
            # self.effective = "It's not very effective... You'll receive hearts if the poke is defeated!"
            self.effective = "It's not Very Effective... You will get a Spooky Chest if the Pokemon is defeated."
        else:
            # self.effective = "It had no effect... You will only get Snowflakes if the poke is defeated."
            # self.effective = "It had no effect... You'll receive hearts if the poke is defeated!"
            self.effective = "It had No Effect... You will get a 1-5 :candy:  if the Pokemon is defeated."

    async def callback(self, interaction):
        self.view.attacked[interaction.user] = self.damage
        await interaction.response.send_message(
            content=f"You used {self.move}. {self.effective}", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Events(bot))
