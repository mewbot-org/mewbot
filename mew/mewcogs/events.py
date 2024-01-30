import os
import discord
import random
import asyncio
import time

from unicodedata import name
from discord.ext import commands
from mewcogs.pokemon_list import *
from mewutils.checks import tradelock, check_mod
from mewutils.misc import get_file_name, get_emoji, ConfirmView, MenuView, pagify
from collections import defaultdict
from datetime import datetime
from typing import Literal
from dataclasses import dataclass

ORANGE = 0xF4831B
RED_GREEN = [0xBB2528, 0x146B3A]
XMAS_ROLE = 1184182751067377674

GLEAM_POKEMON = [
    'Cutiefly', 
    'Flabebe', 
    'Darkrai', 
    'Larvitar', 
    'Scraggy', 
    'Nihilego', 
    'Cleffa', 
    'Zeraora', 
    'Cresselia', 
    'Shaymin', 
    'Dratini', 
    'Wooper', 
    'Wurmple', 
    'Lunatone', 
    'Reshiram', 
    'Meltan', 
    'Zapdos-galar', 
    'Charmander', 
    'Deerling', 
    'Unown', 
    'Pancham', 
    'Corphish', 
    'Kyogre', 
    'Cyndaquil', 
    'Ralts', 
    'Magikarp', 
    'Heracross', 
    'Drowzee', 
    'Porygon', 
    'Shellder', 
    'Chingling', 
    'Entei', 
    'Zapdos', 
    'Weedle', 
    'Mawile', 
    'Omanyte',
    'Anorith', 
    'Togepi', 
    'Torkoal', 
    'Bellsprout', 
    'Piplup', 
    'Treecko', 
    'Axew', 
    'Clamperl', 
    'Scyther', 
    'Latios', 
    'Deoxys', 
    'Poliwag', 
    'Roggenrola', 
    'Yveltal', 
    'Liligant', 
    'Landorus', 
    'Aegislash', 
    'Infernape', 
    'Gastrodon', 
    'Chesnaught', 
    'Zoroark', 
    'Arceus', 
    'Pheromosa', 
    'Rotom', 
    'Goomy', 
    'Milcery', 
    'Minccino', 
    'Turtwig', 
    'Salandit', 
    'Scorbunny', 
    'Dreepy', 
    'Tornadus', 
    'Genesect', 
    'Groudon', 
    'Xurkitree', 
    'Popplio', 
    'Litten', 
    'Chikorita', 
    'Noibat', 
    'Sneasel', 
    'Impidimp', 
    'Eternatus', 
    'Mudkip', 
    'Zacian', 
    'Giratina', 
    'Dracovish', 
    'Budew ', 
    'Spritzee ', 
    'Koraidon ', 
    'Vulpix-alola ', 
    'Teddiursa', 
    'Skarmory',
    'Solosis', 
    'Hawlucha', 
    'Sentret', 
    'Diancie', 
    'Audino', 
    'Tapu-fini', 
    'Suicune', 
    'Froakie',
]

RADIANT_POKEMON = [
    'Necrozma',
    'Yveltal',
    'Salamence',
    'Xerneas',
    'Eevee',
    'Charmander',
    'Celebi',
    'Riolu',
    'Rockruff',
    'Zorua',
    'Dreepy',
    'Lapras',
    'Tyrantrum',
    'Mimikyu',
    'Jynx'
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
                label="Maleskier",
                emoji="<:skier_trainer_male:1184275356606267472>"
            ),
            discord.SelectOption(
                label="Femaleskier",
                emoji="<:skier_trainer_female:1184275354324582420>"
            ),
            discord.SelectOption(
                label="Pyrce",
                emoji="<:pyrce_trainer:1184275351749283850>"
            )
        ]
        super().__init__(
            options=options
        )

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
        self.CHRISTMAS_COMMANDS = True
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
            "Dialga"
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
            "Pheromosa",
            "Stakataka",
            "Celesteela",
            "Guzzlord",
            "Poipole",
            "Kartana",
            "Nihilego",
            "Blacephalon",
            "Xurkitree",
            "Buzzwole",
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
    async def easter(self, ctx: commands.Context):
        ...

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
                embed.set_image(
                    url="https://mewbot.xyz/eastereggs.png"
                )
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

    #@commands.hybrid_group()
    async def summer(self, ctx: commands.Context):
        ...

    #@summer.command(name="shop")
    async def summer_shop(self, ctx):
        """Check the summer shop."""
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the Summer Season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            try:
                event_data = await pconn.fetchrow(
                    "SELECT milk, event_limit FROM events_new WHERE u_id = $1",
                    ctx.author.id,
                )
                raffle_count = await pconn.fetchval(
                    "SELECT raffle FROM users WHERE u_id = $1", ctx.author.id
                )
                milk_count = event_data["milk"]
                event_limit = event_data["event_limit"]
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
            inline=False,
        )
        embed.add_field(
            name="Multipliers",
            value=(
                "`3.` 2x Battle Multi ⏫\n**Cost**: 50 🥛"
                "\n`4.` 2x Shiny Multi ⏫\n**Cost**: 50 🥛"
            ),
            inline=False,
        )
        embed.add_field(
            name="Misc",
            value=(
                f"`5.` 1 Raffle Entry\n**Cost**: 100 🥛 - **Entries**: {raffle_count}"
                "\n`6.` Random Summer Skin\n**Cost**: 100 🥛"
            ),
            inline=False,
        )
        embed.set_thumbnail(
            url="https://archives.bulbagarden.net/media/upload/thumb/9/91/Moomoo_Milk_anime.png/800px-Moomoo_Milk_anime.png"
        )
        embed.set_footer(text="Use /summer buy with an option number to buy that item!")
        await ctx.send(embed=embed)

    #@summer.command(name="buy")
    async def summer_buy(self, ctx, option: int):
        """Buy an item from the summer event shop"""
        if not self.SUMMER_COMMANDS:
            await ctx.send("This command can only be used during the summer season!")
            return
        # User can't participate in event
        # if ctx.author.id == 1075429458271547523:
        # return
        if option < 1 or option > 6:
            await ctx.send(
                "That isn't a valid option. Select a valid option from `/summer shop`."
            )
            return
        if ctx.author.id in self.purchaselock:
            await ctx.send("Sorry, finish any pending purchases first.")
            return
        self.purchaselock.append(ctx.author.id)

        async with self.bot.db[0].acquire() as pconn:
            event_data = await pconn.fetchrow(
                "SELECT milk, event_limit FROM events_new WHERE u_id = $1",
                ctx.author.id,
            )
            milk = event_data["milk"]
            limit = event_data["event_limit"]

            if milk == 0:
                await ctx.send("You haven't gotten any 🥛 yet!")
                return

            if option == 1:
                if limit >= 100:
                    await ctx.send("You've reached the daily purchase limit.")
                    self.purchaselock.remove(ctx.author.id)
                    return

                if milk < 50:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return

                milk -= 50
                redeem_amount = random.randint(2, 3)
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    redeem_amount,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET milk = $1, event_limit = event_limit + $2 WHERE u_id = $3",
                    milk,
                    redeem_amount,
                    ctx.author.id,
                )
                await ctx.send(f"You bought {redeem_amount} Redeems.")
                self.purchaselock.remove(ctx.author.id)

            if option == 2:
                amount = random.randint(1, 25)
                if milk < 75:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                milk -= 75
                await pconn.execute(
                    "UPDATE events_new SET milk = $1 WHERE u_id = $2",
                    milk,
                    ctx.author.id,
                )
                await ctx.bot.commondb.add_bag_item(
                    ctx.author.id, "radiant_gem", amount, True
                )
                await ctx.send(f"You bought {amount}x gleam gems.")
                self.purchaselock.remove(ctx.author.id)
                return

            if option == 3:
                if milk < 50:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                milk -= 50
                inventory = await pconn.fetchrow(
                    "SELECT u_id, battle_multiplier FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                inventory = dict(inventory)

                if inventory["battle_multiplier"] >= 50:
                    await ctx.send("You're maxed out.")
                    self.purchaselock.remove(ctx.author.id)
                    return

                new_amount = min(inventory.get("battle_multiplier", 0) + 2, 50)
                await pconn.execute(
                    "UPDATE events_new SET milk = $1 WHERE u_id = $2",
                    milk,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE account_bound SET battle_multiplier = $1 WHERE u_id = $2",
                    new_amount,
                    ctx.author.id,
                )
                await ctx.send(f"You bought 2x Battle Multipliers.")
                self.purchaselock.remove(ctx.author.id)
                return

            if option == 4:
                if milk < 50:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                milk -= 50
                inventory = await pconn.fetchrow(
                    "SELECT u_id, shiny_multiplier FROM account_bound WHERE u_id = $1",
                    ctx.author.id,
                )
                inventory = dict(inventory)

                if inventory["shiny_multiplier"] >= 50:
                    await ctx.send("You're maxed out.")
                    self.purchaselock.remove(ctx.author.id)
                    return

                new_amount = min(inventory.get("shiny_multiplier", 0) + 2, 50)
                await pconn.execute(
                    "UPDATE events_new SET milk = $1 WHERE u_id = $2",
                    milk,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE account_bound SET shiny_multiplier = $1 WHERE u_id = $2",
                    new_amount,
                    ctx.author.id,
                )
                await ctx.send(f"You bought 2x Shiny Multipliers.")
                self.purchaselock.remove(ctx.author.id)
                return

            if option == 5:
                if milk < 100:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                milk -= 100
                await pconn.execute(
                    "UPDATE users SET raffle = raffle + 1 WHERE u_id = $1",
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE events_new SET milk = $1 WHERE u_id = $2",
                    milk,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You were given an entry into the Summer Raffle!\nThe raffle will be drawn in the Mewbot Official Server. `\invite`"
                )
                self.purchaselock.remove(ctx.author.id)
                return

            if option == 6:
                if milk < 100:
                    await ctx.send("You don't have enough 🥛 for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                milk -= 100
                skins = await pconn.fetchval(
                    "SELECT skins::json FROM users WHERE u_id = $1", ctx.author.id
                )
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                if pokemon not in skins:
                    skins[pokemon] = {}
                if "summer2023" not in skins[pokemon]:
                    skins[pokemon]["summer2023"] = 1
                else:
                    skins[pokemon]["summer2023"] += 1
                await pconn.execute(
                    "UPDATE events_new SET milk = $1 WHERE u_id = $2",
                    milk,
                    ctx.author.id,
                )
                await pconn.execute(
                    "UPDATE users SET skins = $1::json WHERE u_id = $2",
                    skins,
                    ctx.author.id,
                )
                await ctx.send(
                    f"You got a {pokemon} summer skin! Apply it with `/skin apply`."
                )
                self.purchaselock.remove(ctx.author.id)
                return

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
                    "Successfully bought 1 <:mewbot_potion:1036332369076043776> for 50 <:mewbot_candy:1036332371038982264>."
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
                    await ctx.send("Successfully bought a raffle ticket for 1 <:mewbot_mask:1036332369818431580>!")
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
                    "Successfully bought a raffle ticket for 1 <:mewbot_mask:1036332369818431580>!"
                )
                return
            # Everything from this point below uses Potions as currency
            # Checks balance per price as below.
            price = [100, 8, 5, 25, 80][option - 2]
            if bal["potion"] < price:
                await ctx.send(
                    "You don't have enough <:mewbot_potion:1036332369076043776> for that!"
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
                    f"Successfully bought 1 Scary for {price} <:mewbot_potion:1036332369076043776>."
                )
            # Spooky Chest
            if option == 4:
                await pconn.execute(
                    "UPDATE events_new SET spooky_chest = spooky_chest + $1 WHERE u_id = $2",
                    1,
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought a Spooky Chest for {price} <:mewbot_potion:1036332369076043776>."
                )
            # Fleshy Chest
            elif option == 5:
                await pconn.execute(
                    "UPDATE events_new SET fleshy_chest = fleshy_chest + $1 WHERE u_id = $2",
                    1,
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought a Fleshy Chest for {price} <:mewbot_potion:1036332369076043776>."
                )
            # Horrific Chest
            elif option == 6:
                await pconn.execute(
                    "UPDATE events_new SET horrific_chest = horrific_chest + $1 WHERE u_id = $2",
                    1,
                    ctx.author.id,
                )
                await ctx.send(
                    f"Successfully bought a Horrific Chest for {price} <:mewbot_potion:1036332369076043776>."
                )

    #@halloween.command(name="inventory")
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
            name="Currency",
            value=(
                f"{data['candy']}x Candy <:mewbot_candy:1036332371038982264>\n"
                f"{data['potion']}x Sus Potions <:mewbot_potion:1036332369076043776>\n"
                f"{data['pumpkin']}x Scary Pumpkins <:mewbot_mask:1036332369818431580>\n"
            ),
            inline=True
        )
        embed.add_field(
            name="Chests",
            value=(
                f"{data['spooky_chest']}x Spooky\n"
                f"{data['fleshy_chest']}x Fleshy\n"
                f"{data['horrific_chest']}x Horrific\n"
            ),
            inline=True
        )

        embed.set_footer(
            text="Join Mewbot's Official Server for all event updates!"
        )
        await ctx.send(embed=embed)

    #@halloween.command(name="shop")
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
            description="Use /halloween buy with an option number to buy that item!",
        )
        embed.add_field(
            name="1. 1 Sus Potion",
            value="50 <:mewbot_candy:1036332371038982264>",
            inline=True,
        )
        embed.add_field(
            name="2. 1 Pumpkin",
            value="100 <:mewbot_potion:1036332369076043776>",
            inline=True,
        )
        embed.add_field(
            name="3. 1 Raffle Entry",
            value="1 <:mewbot_mask:1036332369818431580>",
            inline=True,
        )
        embed.add_field(
            name="4. Spooky Chest",
            value="5 <:mewbot_potion:1036332369076043776>",
            inline=True,
        )
        embed.add_field(
            name="5. Fleshy Chest",
            value="25 <:mewbot_potion:1036332369076043776>",
            inline=True,
        )
        embed.add_field(
            name="6. Horrific Chest",
            value="80 <:mewbot_potion:1036332369076043776>",
            inline=True,
        )
        # embed.add_field(
        # name="7. Missingno",
        # value="1 <:mewbot_mask:1036332369818431580>",
        # inline=True
        # )
        # embed.add_field(
        # name="8. Halloween Radiant",
        # value="1 <:mewbot_mask:1036332369818431580>",
        # inline=True
        # )
        embed.set_footer(text="Use /halloween inventory to check your stash!")
        await ctx.send(embed=embed)

   # @halloween.command(name="open_spooky")
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
                ("gleam", "missingno", "cred", "trick"),
                weights=(0.03, 0.18, 0.3, 0.4),
            )[0]
            if reward == "gleam":
                #Chance of Zoroark trick
                chance_int = random.randint(1, 100)
                if chance_int > 90:
                    pokemon = 'Zoroark'
                    msg = f"**Trick!** You received a **{pokemon}!**\n"
                    skin = None
                else:
                    pokemon = random.choice(self.HALLOWEEN_RADIANT)
                    msg = f"**Treat!** You received a Halloween **{pokemon}!**\n"
                    skin = "halloween2023"
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, skin=skin
                )
            #Redeems removed as event rewards
            #elif reward == "redeem":
                #amount = random.randint(1, 3)
                #async with ctx.bot.db[0].acquire() as pconn:
                    #await pconn.execute(
                        #"UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                        #amount,
                        #ctx.author.id,
                    #)
                #msg = f"You received {amount} redeem!\n"
            elif reward == "cred":
                amount = random.randint(35, 65) * 1000
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
        msg += f"You also received {candy} <:mewbot_candy:1036332371038982264>!\n"
        await ctx.send(msg)

    #@halloween.command(name="open_fleshy")
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
                ("gleam", "rarechest", "mythicchest", "missingno", "trick"),
                weights=(0.32, 0.15, 0.05, 0.16, 0.32),
            )[0]

            if reward == "gleam":
                #Chance of Zoroark trick
                chance_int = random.randint(1, 100)
                if chance_int > 90:
                    pokemon = 'Zoroark'
                    msg = f"**Trick!** You received a **{pokemon}!**\n"
                    skin = None
                else:
                    pokemon = random.choice(self.HALLOWEEN_RADIANT)
                    msg = f"**Treat!** You received a Halloween **{pokemon}!**\n"
                    skin = "halloween2023"
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, skin=skin
                )

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
        msg += f"You also received {potions} <:mewbot_potion:1036332369076043776>!\n"
        await ctx.send(msg)

    #@halloween.command(name="open_horrific")
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
                ("legendchest", "boostedshiny", "gleam", "trick"),
                weights=(0.155, 0.3, 0.236, 0.30),
            )[0]
            if reward == "boostedshiny":
                #Chance of Zoroark trick
                chance_int = random.randint(1, 100)
                if chance_int > 90:
                    pokemon = 'Zoroark'
                    boosted = False
                    msg = f"**Trick!** You received a **{pokemon}!**\n"
                    shiny = False
                else:
                    pokemon = random.choice(await self.get_ghosts())
                    boosted = True
                    msg = f"**Treat!** You received a Shiny Boosted **{pokemon}!**\n"
                    shiny = True
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, boosted=boosted, shiny=shiny
                )
            elif reward == "gleam":
                #Chance of Zoroark trick
                chance_int = random.randint(1, 100)
                if chance_int > 90:
                    pokemon = 'Zoroark'
                    boosted = False
                    msg = f"**Trick!** You received a **{pokemon}!**\n"
                    skin = None
                else:
                    pokemon = random.choice(self.HALLOWEEN_RADIANT)
                    boosted = True
                    msg = f"**Treat!** You received a Boosted Halloween **{pokemon}**!\n"
                    skin = "halloween2023"

                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, skin=skin, boosted=boosted
                )
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
        potions = random.randint(5, 10)
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE events_new SET potion = potion + $1 WHERE u_id = $2",
                potions,
                ctx.author.id,
            )
        msg += f"You also received {potions} <:mewbot_potion:1036332369076043776>!\n"
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

    @commands.hybrid_group()
    async def christmas(self, ctx):
        """Christmas commands."""
        pass

    @christmas.command(name="leaderboard")
    async def leaderboard(self, ctx, board: Literal['Staff', 'User'], type:Literal['thrown', 'hit']):
        if type == 'thrown':
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
                    #if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                        #continue
                    tnick, staff = await pconn.fetchrow(
                        "SELECT tnick, staff FROM users WHERE u_id = $1", id
                    )
                    exp = exps[idx]
                    if board == 'Staff':
                        if id == 744831273406824449:
                            pass
                        elif staff not in ('Admin', 'Mod', 'Investigator'):
                            continue
                    elif board == 'User':
                        if staff != 'User' or id == 744831273406824449:
                            continue
                    else:
                        await ctx.send("That is not a valid event leaderboard type, please try again...")
                        return
                    if tnick is not None:
                        name = f"{tnick} - ({id})"
                    else:
                        name = f"Unknown user - ({id})"
                    desc += f"__{true_idx}__. `Position` : **{exp}** - `{name}`\n"
                    true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        elif type == 'hit':
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
                    #if staffs[idx] == "Developer" or ids[idx] in LEADERBOARD_IMMUNE_USERS:
                        #continue
                    tnick, staff = await pconn.fetchrow(
                        "SELECT tnick, staff FROM users WHERE u_id = $1", id
                    )
                    exp = exps[idx]
                    if board == 'Staff':
                        if id == 744831273406824449:
                            pass
                        elif staff not in ('Admin', 'Mod', 'Investigator'):
                            continue
                    elif board == 'User':
                        if staff != 'User' or id == 744831273406824449:
                            continue
                    else:
                        await ctx.send("That is not a valid event leaderboard type, please try again...")
                        return
                    if tnick is not None:
                        name = f"{tnick} - ({id})"
                    else:
                        name = f"Unknown user - ({id})"
                    desc += f"__{true_idx}__. `Position` : **{exp}** - `{name}`\n"
                    true_idx += 1
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()

    @christmas.command(name="snowball")
    async def throw_snowball(self, ctx, player:discord.Member):
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
            snowballs, times_hit, times_thrown, trainer_redeemed, role_redeemed = await pconn.fetchrow(
                "SELECT snowballs, times_hit, times_thrown, trainer_redeemed, role_redeemed FROM events_new WHERE u_id = $1",
                ctx.author.id
            )
            if snowballs is None:
                await ctx.send("You have not started the event!")
                return
            elif snowballs < 1:
                await ctx.send("You have to get some snowballs <:snowballs:1184292806190182420>!")
                return
            
            attacked_times_hit = await pconn.fetchval(
                "SELECT times_hit FROM events_new WHERE u_id = $1",
                player.id
            )
            if attacked_times_hit is None:
                #Meaning player hit hasn't started event
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING", player.id
                )
                await ctx.send("Please try this command again shortly...")
                return
                        
            #Let's hit player
            await pconn.execute(
                "UPDATE events_new SET times_hit = times_hit + 1 WHERE u_id = $1",
                player.id
            )
            #Remove snowball and update stats
            snowballs -= 1
            times_thrown += 1
            await pconn.execute(
                "UPDATE events_new SET snowballs = $1, times_thrown = $2 WHERE u_id = $3",
                snowballs,
                times_thrown,
                ctx.author.id
            )
            if times_thrown >= 100 and role_redeemed is False:
                event_role = ctx.guild.get_role(1184182751067377674)
                await ctx.author.add_roles(
                    event_role, reason=f"Event threshold reward - {ctx.author}"
                )
                await pconn.execute(
                    "UPDATE events_new SET role_redeemed = True WHERE u_id = $1",
                    ctx.author.id
                )
                msg += "You've received the Xmas2023 Official Server Role!"
            elif times_thrown >= 250 and trainer_redeemed is False:
                choice = await ListSelectView(
                    ctx, "Please choose a trainer image!"
                ).wait()
                if choice is None:
                    await ctx.send("You did not select in time, cancelling.")
                    self.purchaselock.remove(ctx.author.id)
                    return
                trainer_images = await pconn.fetchval(
                    "SELECT trainer_images::json FROM account_bound WHERE u_id = $1",
                    ctx.author.id
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
                    ctx.author.id
                )
                await pconn.execute(
                    "UPDATE events_new SET trainer_redeemed = True WHERE u_id = $1",
                    ctx.author.id
                )
                msg += f"You've successfully redeemed {choice} as your trainer image!\nIt's been added to your trainer image inventory."

        embed = discord.Embed(
            title="Mewbot Christmas",
            description=f"You've throw a snowball!\nDid it hit?!",
            color=0x0084FD
        )
        embed.add_field(
            name="Victim",
            value=f"You've hit **{player.name}**!",
            inline=False
        )
        embed.add_field(
            name=f"{ctx.author.name}'s Stats",
            value=f"You've been hit __{times_hit} times__.\nYou've thrown __{times_thrown} snowballs__!",
            inline=False
        )
        if msg != "":
            embed.add_field(
                name="Rewards",
                value=f"{msg}",
                inline=False
            )
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

    @christmas.command(name="buy")
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
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Not available at the moment!")
            #return
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
                await ctx.send("You haven't started! Please use `/start` to start your adventure!")
                return
            
            radiant_gems, battle_multiplier, shiny_multiplier = await pconn.fetchrow(
                "SELECT radiant_gem, battle_multiplier, shiny_multiplier FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if radiant_gems is None:
                await ctx.send("No bound items table found. Have you started or converted to the new bag system if needed?")
                return
            
            gleam_limit, radiant_limit = await pconn.fetchrow(
                "SELECT gleam_limit, radiant_limit FROM events_new WHERE u_id = $1",
                ctx.author.id
            )
            if gleam_limit is None:
                #Try to add user to table and then have them redo the command
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING", ctx.author.id
                )
                await ctx.send("Please retry the command.")
                return

            self.purchaselock.append(ctx.author.id)

            #Battle Multiplier
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
            
            #Shiny Multiplier
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
            
            #Gleam Gems
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
                    ctx.author.id
                )
                await ctx.send(f"You bought {earned_gleams}x Gleam Gems <a:radiantgem:774866137472827432>.")
                self.purchaselock.remove(ctx.author.id)
                return
            
            #Event Gleams
            #Gives the skin for the Pokemon rather than the Pokemon
            if option == 4:
                if radiant_gems < 150:
                    await ctx.send("You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!")
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

            #Boosted Event Glems
            #This gives Pokemon w/skin rather than just skin
            if option == 5:
                if radiant_gems < 300:
                    await ctx.send("You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                radiant_gems -= 300
                pokemon = random.choice(self.EVENT_POKEMON).lower()
                await pconn.execute(
                    "UPDATE account_bound SET radiant_gem = $1 WHERE u_id = $2",
                    radiant_gems,
                    ctx.author.id,
                )
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon.capitalize(), boosted=True, skin='xmas2023')
                await ctx.send(
                    f"You got a **{pokemon.title()} Christmas Pokemon**!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            #Returning Gleams
            if option == 6:
                if radiant_gems < 300:
                    await ctx.send("You don't have enough Gleam Gems <a:radiantgem:774866137472827432> for that!")
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
                    ctx.author.id
                )
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon.capitalize(), skin='gleam')
                await ctx.send(
                    f"You got a **<:gleam:1010559151472115772> {pokemon.title()} **!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

            #Returning Radiants
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
                    ctx.author.id
                )
                await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon.capitalize(), skin='radiant')
                await ctx.send(
                    f"You got a **<:radiant:1010558960027308052> {pokemon.title()} **!\nIt's been added to your list."
                )
                self.purchaselock.remove(ctx.author.id)
                return

    @christmas.command(name="inventory")
    async def christmas_inventory(self, ctx):
        """Check your christmas inventory."""
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Not available at the moment!")
            #return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchrow(
                "SELECT snowflakes, small_gift, large_gift, snowballs, times_hit, times_thrown FROM events_new WHERE u_id = $1", \
                ctx.author.id
            )
        embed = discord.Embed(
            title=f"{ctx.author.name.title()}'s Christmas Inventory",
            description=f"These are all items that are related to the event.\nGet all of these items from RAIDS!",
            color=random.choice(RED_GREEN),
        )
        embed.add_field(
            name="Snowballs <:snowballs:1184292806190182420>", 
            value=f"**Available**: {inventory['snowballs']}x\n**Times Hit**: {inventory['times_hit']}\n**Times Thrown**: {inventory['times_thrown']}",
            inline=False
        )
        embed.add_field(
            name="Presents", 
            value=(
                f"**Small Present** 📦: {inventory['small_gift']}x\n"
                f"**Large Present** 🎁: {inventory['large_gift']}x"
            ),
            inline=False
        )
        # if "holiday cheer" in inventory:
        # embed.add_field(name="Holiday Cheer",
        # value=f"{inventory['holiday cheer']}x")
        embed.set_footer(text="Happy Holidays!")
        await ctx.send(embed=embed)

    @christmas.command(name="shop")
    async def christmas_shop(self, ctx):
        """Check the christmas shop."""
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Not available at the moment!")
            #return

        event_data = await ctx.bot.db[0].fetchrow(
            "SELECT radiant_limit, gleam_limit FROM events_new WHERE u_id = $1",
            ctx.author.id
        )
        if event_data is None:
            radiant_limit = 0
            gleam_limit = 0
        else:
            radiant_limit = event_data['radiant_limit']
            gleam_limit = event_data['gleam_limit']

        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        
        #This was the original event shop.
        #desc = (
            #"**Option# | Price | Item**\n"
            #"**1** | 25 <:snowflake:1055702885041721374> | 1 Redeems\n"
            #"**2** | 50 <:snowflake:1055702885041721374> | 2x Battle Multi\n"
            #"**3** | 50 <:snowflake:1055702885041721374> | 2x Shiny Multi\n"
            #"**4** | 75 <:snowflake:1055702885041721374> | 1-25 Gleam Gems\n"
            #"**5** | 100 <:snowflake:1055702885041721374> | 1x Raffle Entry\n"
            #"**6** | 150 <:snowflake:1055702885041721374> | Random Christmas Skin\n"
           #""
        #)

        #2023 remake
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
            inline=False
        )
        embed.add_field(
            name="Currencies",
            value=(
                "`3.` __1-25 Gleam Gems.__\n**Cost:** 50,000 <:mewcoin:1010959258638094386>\n"
            ),
            inline=False
        )
        embed.add_field(
            name="Gleams",
            value=(
                "`4.` __Event Skin__\n**Cost:** 150 <a:radiantgem:774866137472827432>\nThis is a skin that goes into inventory!\n"
                "`5.` __Boosted Event Skin__\n**Cost:** 300 <a:radiantgem:774866137472827432>\nThis is a Pokemon already with the skin equipped!"
            ),
            inline=False
        )
        embed.add_field(
            name="Returning Gleams",
            value=(
                "`6.` __Returning Gleams__\n"
                "**Cost:** 300 <a:radiantgem:774866137472827432>\n"
                f"Purchase Limit: {gleam_limit} / 50\nGleams from 2023."
            ),
            inline=False
        )
        embed.add_field(
            name="Returning Radiants",
            value=(
                "`7.` __Returning Radiants__\n"
                "**Cost:** 200 <:redeem:1037942226132668417>\n"
                f"Purchase Limit: {radiant_limit} / 20\n"
                ""
            ),
            inline=False
        )
        embed.set_footer(
            text="Use /christmas buy to buy an item!"
        )
        await ctx.send(embed=embed)

    @christmas.command(name="smallgift")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def open_smallgift(self, ctx):
        """Open a small christmas gift."""
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Sorry, this is not available yet")
            #return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            small_gift = await pconn.fetchval(
                "SELECT small_gift FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if small_gift is None:
                await ctx.send(f"You have not Started or participated in the event yet!\nStart with `/start` first!")
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
            await ctx.bot.commondb.create_poke(
                ctx.bot, ctx.author.id, pokemon
            )
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
            msg = (
                "You stole some of Santa's cookies and milk! It restored some npc energy!\n"
            )
        await ctx.send(msg)

    @christmas.command(name="largegift")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def open_largegift(self, ctx):
        """Open a large christmas gift."""
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Sorry, this is not available yet")
            #return
        if not self.CHRISTMAS_COMMANDS:
            await ctx.send("This command can only be used during the christmas season!")
            return
        async with ctx.bot.db[0].acquire() as pconn:
            large_gift = await pconn.fetchval(
                "SELECT large_gift FROM events_new WHERE u_id = $1", ctx.author.id
            )
            if large_gift is None:
                await ctx.send(f"You have not Started or participated in the event yet!\nStart with `/start` first!")
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
            await ctx.bot.commondb.add_bag_item(
                ctx.author.id,
                chest,
                1,
                True
            )
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

    async def give_candy(self, channel, user):
        """Gives candy to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id,
            )
            await pconn.execute(
                "UPDATE events_new SET candy = candy + $1 WHERE u_id = $2",
                random.randint(1, 3),
                user.id,
            )
        await channel.send(
            f"The pokemon dropped some candy!\nUse command `/halloween inventory` to view what you have collected."
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

    async def give_scary_mask(self, channel, user):
        """Gives jack-o-laterns to the provided user."""
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "INSERT INTO halloween (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id,
            )
            await pconn.execute(
                "UPDATE halloween SET pumpkin = pumpkin + $1 WHERE u_id = $2",
                random.randint(1, 2),
                user.id,
            )
        await channel.send(
            f"The pokemon dropped a scary mask!\nUse command `/halloween inventory` to view what you have collected."
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
        await asyncio.sleep(random.randint(30, 45))
        await ChristmasSpawn(self, channel, random.choice(self.EVENT_POKEMON)).start()

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
            ),
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
            if not random.randrange(10):
                await self.give_candy(channel, user)
            if not random.randrange(5) or user.id == 334155028170407949:
                await self.maybe_spawn_christmas(channel)
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
                await self.maybe_spawn_christmas(channel)

        # if not random.randrange(10):
        # await self.maybe_spawn_unown(channel)

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
        # if not random.randrange(7):
        # await self.maybe_spawn_unown(channel)


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
            "http://mewbot.xyz/sprites/"
            + await get_file_name(self.poke, self.cog.bot, skin="xmas2023")
        )
        guild = await self.cog.bot.mongo_find("guilds", {"id": self.channel.guild.id})
        if guild is None:
            small_images = False
        else:
            small_images = guild["small_images"]
        self.embed = discord.Embed(
            title="A Christmas Pokémon Appears!",
            description="Join the battle to take it down.",
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
                title="The Christmas Pokémon ran away!",
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
                {"type_id": {"$in": super_types}, "damage_class_id": {"$ne": 1}, "id": {"$nin": uncoded_ids}}
            )
            .to_list(None)
        )
        super_moves = [
            x["identifier"].capitalize().replace("-", " ") for x in super_raw
        ]
        normal_raw = (
            await self.cog.bot.db[1]
            .moves.find(
                {"type_id": {"$in": normal_types}, "damage_class_id": {"$ne": 1}, "id": {"$nin": uncoded_ids}}
            )
            .to_list(None)
        )
        normal_moves = [
            x["identifier"].capitalize().replace("-", " ") for x in normal_raw
        ]
        un_raw = (
            await self.cog.bot.db[1]
            .moves.find({"type_id": {"$in": un_types}, "damage_class_id": {"$ne": 1}, "id": {"$nin": uncoded_ids}})
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
                #If you don't want type emotes, uncomment below
                #and comment out what's below it
                #moves.append(RaidMoveNoEmote(move_name, 2))

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
                #moves.append(RaidMoveNoEmote(move_name, 1))

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
                #moves.append(RaidMoveNoEmote(move_name, 0))

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
                #moves.append(RaidMoveNoEmote(move_name, 0))

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

        self.max_hp = int(len(self.registered) * 1.25)
        self.embed = discord.Embed(
            title="A Christmas Pokémon has spawned, attack it with everything you've got!",
            color=0x0084FD,
        )
        self.embed.add_field(name="-", value=f"HP = {self.max_hp}/{self.max_hp}")
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
                title="The Christmas Pokémon got away!",
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
                await pconn.execute(
                    "INSERT INTO events_new (u_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    attacker.id,
                )
                if damage == 2:
                    await pconn.execute(
                        "UPDATE events_new SET large_gift = large_gift + $1 WHERE u_id = $2",
                        1,
                        attacker.id,
                    )
                elif damage == 1:
                    await pconn.execute(
                        "UPDATE events_new SET small_gift = small_gift + $1 WHERE u_id = $2",
                        1,
                        attacker.id,
                    )
                elif damage == 0:
                    await pconn.execute(
                        "UPDATE events_new SET snowballs = snowballs + $1 WHERE u_id = $2",
                        random.randint(1, 2),
                        attacker.id,
                    )

        self.embed = discord.Embed(
            title=f"The Christmas Pokémon was defeated!\n Attackers have been awarded. {extra_msg}",
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

#Has the Type Emote on Button
class RaidMove(discord.ui.Button):
    """A move button for attacking a christmas pokemon."""

    def __init__(self, move, damage, emote):
        super().__init__(label=move, emoji=emote, style=discord.ButtonStyle.gray)
        self.move = move
        self.damage = damage
        self.emote = emote

        if damage == 2:
            # self.effective = "It's super effective! You will get a Large Present if the poke is defeated."
            # self.effective = "It's super effective! You'll receive hearts if the poke is defeated!"
            self.effective = f"It's Super Effective! You will get a Large Gift 🎁 if the Pokemon is defeated."
        elif damage == 1:
            # self.effective = "It's not very effective... You will get a Small Present if the poke is defeated."
            # self.effective = "It's not very effective... You'll receive hearts if the poke is defeated!"
            self.effective = f"It's not Very Effective... You will get a Small Gift 📦 if the Pokemon is defeated."
        else:
            # self.effective = "It had no effect... You will only get Snowflakes if the poke is defeated."
            # self.effective = "It had no effect... You'll receive hearts if the poke is defeated!"
            self.effective = (
                f"It had No Effect... You will get a 1-2 <:snowballs:1184292806190182420> Snowballs if the Pokemon is defeated."
            )

    async def callback(self, interaction):
        self.view.attacked[interaction.user] = self.damage
        await interaction.response.send_message(
            content=f"You used {self.move}. {self.effective}", ephemeral=True
        )

#No type emote on button
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
            self.effective = (
                "It had No Effect... You will get a 1-5 <:mewbot_candy:1036332371038982264> if the Pokemon is defeated."
            )

    async def callback(self, interaction):
        self.view.attacked[interaction.user] = self.damage
        await interaction.response.send_message(
            content=f"You used {self.move}. {self.effective}", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Events(bot))
