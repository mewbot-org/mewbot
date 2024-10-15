'''
All code here is copyrighted by Foreboding aka Foreboding#5794 on Discord. Should be used exclusively for the Onixian bot
Please refer to GitHub repo for copyright usage
'''
import random
import string
import discord
import aiohttp

from discord import Webhook
from mewcogs.pokemon_list import natlist

async def get_moves(ctx, pokemon_name):
    if pokemon_name == "smeargle":
        # Below list are for reference as to why each ID is in unselectable_ids
        # Moves which are not coded in the bot
        uncodded_moves = [
            266, 270, 476, 495, 502, 511, 597, 602, 603, 607, 622, 623, 624, 625, 626, 627,
            628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643,
            644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 671,
            695, 696, 697, 698, 699, 700, 701, 702, 703, 719, 723, 724, 725, 726, 727, 728,
            811, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10009, 10010, 10011,
            10012, 10013, 10014, 10015, 10016, 10017, 10018
        ]
        # These moves fail if user's pokemon doesn't have a held item
        held_item_moves = [
            278, 282, 343, 363, 365, 373, 374, 415, 450, 478, 510, 516, 734, 810, 
        ]
        # Total list of moves that can't be selected by pokemon_generator
        unselectable_ids = [
            266, 270, 476, 495, 502, 511, 597, 602, 603, 607, 622, 623, 624, 625, 626, 627,
            628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643,
            644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 671,
            695, 696, 697, 698, 699, 700, 701, 702, 703, 719, 723, 724, 725, 726, 727, 728,
            811, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10009, 10010, 10011,
            10012, 10013, 10014, 10015, 10016, 10017, 10018, 278, 282, 343, 363, 365, 373, 374, 
            415, 450, 478, 510, 516, 734, 810, 33 #Tackle
        ]
        all_moves = await ctx.bot.db[1].moves.find({
            "id": {"$nin": unselectable_ids},
        }).to_list(None)
        return [t["identifier"] for t in all_moves]
    moves = await ctx.bot.db[1].pokemon_moves.find_one({"pokemon": pokemon_name})
    if moves is None:
        return None
    moves = moves["moves"]
    new_moves = list(set(moves))
    new_moves.sort()
    return new_moves


#This should provide 4 moves dependent on entered Pokemon's typage and .
async def move_generator(self, npc_pokemon:str, user_pokemon:str):
    """This takes a Pokemon name and provides optimal moveset"""
    #First we have to pull Pokemon's moveset to verify move is usable
    move_pool = await get_moves(self, npc_pokemon)

    form_info = await self.bot.db[1].forms.find_one({"identifier": user_pokemon.lower()})
    type_ids = (await self.bot.db[1].ptypes.find_one({"id": form_info["pokemon_id"]}))["types"]
    type_effectiveness = {}
    for te in await self.bot.db[1].type_effectiveness.find({}).to_list(None):
        type_effectiveness[(te["damage_type_id"], te["target_type_id"])] = te["damage_factor"]

    #Prepare effectiveness of each type in relation to Dialga
    super_types = []
    normal_types = []
    un_types = []
    for attacker_type in range(1, 19):
        effectiveness = 1
        for defender_type in type_ids:
            effectiveness *= type_effectiveness[(attacker_type, defender_type)] / 100
            #print(effectiveness)
        if effectiveness > 1:
            super_types.append(attacker_type)
        elif effectiveness < 1:
            un_types.append(attacker_type)
        else:
            normal_types.append(attacker_type)

    #Go through and pull moves depending on type effectiveness
    super_raw = await self.bot.db[1].moves.find({"type_id": {"$in": super_types}, "damage_class_id": {"$ne": 1}}).to_list(None)
    super_moves = [x["identifier"] for x in super_raw]
    normal_raw = await self.bot.db[1].moves.find({"type_id": {"$in": normal_types}, "damage_class_id": {"$ne": 1}}).to_list(None)
    normal_moves = [x["identifier"] for x in normal_raw]
    #We are not adding non-effective moves to NPC battles
    #un_raw = await _ctx.bot.db[1].moves.find({"type_id": {"$in": un_types}, "damage_class_id": {"$ne": 1}}).to_list(None)
    #un_moves = [x["identifier"].capitalize().replace("-", " ") for x in un_raw]

    # Add the moves to the move array
    moves = []

    for move in super_moves:
        if move in move_pool:
            count = len(moves)
            if count <= 1:
                moves.append(move)

    for move in normal_moves:
        if move in move_pool:
            count = len(moves)
            if count <= 3:
                moves.append(move)

    random.shuffle(moves)
    return moves

async def generate_pokemon(self, npc_pokemon, user_pokemon, user_pokemon_level, npc_type=None):
    """Generate NPC Pokemon instead of using ones from database"""
    #Pokemon structure that needs to be passed to duels
    #Would need to follow below structure and return to duel/commands.py
    pokemon = {
        "pokname": None,
        "poknick": None,
        "hpiv": 0,
        "atkiv": 0,
        "defiv": 0,
        "spatkiv": 0,
        "spdefiv": 0,
        "speediv": 0,
        "hpev": 0,
        "defev": 0,
        "atkev": 0,
        "spatkev": 0,
        "spdefev": 0,
        "speedev": 0,
        "pokelevel": 0,
        "shiny": False, 
        "radiant": None,
        "skin": None, 
        "id": 0,
        "hitem": 'None',
        "happiness": 0,
        "moves": [],  
        "ability_index": 0, 
        "nature": "None", 
        "gender": "None",
    }

    self.bot.logger.info(f"POKE'S NAME: {user_pokemon}")

    #Deform pokes that are formed into battle forms that they should not start off in
    if user_pokemon == "Mimikyu-busted":
        user_pokemon = "Mimikyu"
    if user_pokemon in ("Cramorant-gorging", "Cramorant-gulping"):
        user_pokemon = "Cramorant"
    if user_pokemon == "Eiscue-noice":
        user_pokemon = "Eiscue"
    if user_pokemon == "Darmanitan-zen":
        user_pokemon = "Darmanitan"
    if user_pokemon == "Darmanitan-zen-galar":
        user_pokemon = "Darmanitan-galar"
    if user_pokemon == "Aegislash-blade":
        user_pokemon = "Aegislash"
    if user_pokemon in ("Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet"):
        user_pokemon = "Minior"
    if user_pokemon == "Wishiwashi" and user_pokemon_level >= 20:
        user_pokemon = "Wishiwashi-school"
    if user_pokemon == "Wishiwashi-school" and user_pokemon_level < 20:
        user_pokemon = "Wishiwashi"
    if user_pokemon == "Greninja-ash":
        user_pokemon = "Greninja"
    if user_pokemon == "Zygarde-complete":
        user_pokemon = "Zygarde"
    if user_pokemon == "Morpeko-hangry":
        user_pokemon = "Morpeko"
    if user_pokemon == "Cherrim-sunshine":
        user_pokemon = "Cherrim"
    if user_pokemon in ("Castform-snowy", "Castform-rainy", "Castform-sunny"):
        user_pokemon = "Castform"
    if user_pokemon in (
        "Arceus-dragon",
        "Arceus-dark",
        "Arceus-ground",
        "Arceus-fighting",
        "Arceus-fire",
        "Arceus-ice",
        "Arceus-bug",
        "Arceus-steel",
        "Arceus-grass",
        "Arceus-psychic",
        "Arceus-fairy",
        "Arceus-flying",
        "Arceus-water",
        "Arceus-ghost",
        "Arceus-rock",
        "Arceus-poison",
        "Arceus-electric",
    ):
        user_pokemon = "Arceus"
    if user_pokemon in (
        "Silvally-psychic",
        "Silvally-fairy",
        "Silvally-flying",
        "Silvally-water",
        "Silvally-ghost",
        "Silvally-rock",
        "Silvally-poison",
        "Silvally-electric",
        "Silvally-dragon",
        "Silvally-dark",
        "Silvally-ground",
        "Silvally-fighting",
        "Silvally-fire",
        "Silvally-ice",
        "Silvally-bug",
        "Silvally-steel",
        "Silvally-grass",
    ):
        user_pokemon = "Silvally"
    if user_pokemon == "Palafin-hero":
        user_pokemon = "Palafin"
    if user_pokemon in ("Calyrex-shadow-rider", "Calyrex-ice-rider"):
        user_pokemon = "Calyrex"
    if user_pokemon.endswith("-mega-x") or user_pokemon.endswith("-mega-y"):
        user_pokemon = user_pokemon[:-7]
    if user_pokemon.endswith("-mega"):
        user_pokemon = user_pokemon[:-5]
    #TODO: Meloetta, Shaymin

    form_info = await self.bot.db[1].forms.find_one({"identifier": user_pokemon.lower()})
    pokemon_info = await self.bot.db[1].pfile.find_one({"id": form_info["base_id"]})

    #Basic Information
    pokemon['pokname'] = npc_pokemon.lower()
    pokemon['poknick'] = npc_pokemon.lower()
    if random.randint(1, 100) > 10:
        pokemon['shiny'] = True
    pokemon['happiness'] = 255 #Happy mf
    pokemon['nature'] = random.choice(natlist)

    #This uses default npc type for now
    pokemon['moves'] = await move_generator(self, npc_pokemon, user_pokemon)

    #Level Information
    #TODO: Stagger this depending on route entered
    # At the moment it's just players poke's level + 5
    if user_pokemon_level < 100:
        max_lvl = user_pokemon_level + 5
        pokemon['pokelevel'] = random.randint(user_pokemon_level, max_lvl)
    else:
        pokemon['pokelevel'] = 100

    #Held Item
    #TODO: Possibly add held item depending on npc

    #Ability IDs
    ab_ids = (
        await self.bot.db[1]
        .poke_abilities.find({"pokemon_id": form_info["pokemon_id"]})
        .to_list(length=3)
    )
    ab_ids = [doc["ability_id"] for doc in ab_ids]

    #Gender
    try:
        gender_rate = pokemon_info["gender_rate"]
    except TypeError:
        #TODO: Eventually will need exceptions for Pokemon like Urshifu which
        #Are treated as a separate pokemon rather than a form that's deformed.
        if user_pokemon == 'Urshifu-rapid-strike':
            gender_rate = 0

    if "idoran-" in pokemon:
        pokemon['gender'] = pokemon[-2:]
    elif pokemon['pokname'].lower() == "illumise":
        pokemon['gender'] = "-f"
    elif pokemon['pokname'].lower() == "volbeat":
        pokemon['gender'] = "-m"
    # -1 = genderless pokemon
    elif gender_rate == -1:
        pokemon['gender'] = "-x"
    # 0 = male only, 8 = female only, in between means mix at that ratio.
    # 0 < 0 = False, so the poke will always be male
    # 7 < 8 = True, so the poke will always be female
    elif random.randrange(8) < gender_rate:
        pokemon['gender'] = "-f"
    else:
        pokemon['gender'] = "-m"
            
    #Stats
    pokemon['hpiv'] = random.randint(25, 31) #Minimum of 25. 
    pokemon['defiv'] = random.randint(25, 31) #Minimum of 25. 
    pokemon['spatkiv'] = random.randint(25, 31) #Minimum of 25. 
    pokemon['spdefiv'] = random.randint(25, 31) #Minimum of 25. 
    pokemon['speediv'] = random.randint(25, 31) #Minimum of 25. 

    #Pokemon EVs - Leave as 0 for route Pokemon
    pokemon['hpev'] = 0
    pokemon['atkev'] = 0
    pokemon['defev'] = 0
    pokemon['spatkev'] = 0
    pokemon['spdefev'] = 0

    #Generate ID that will be printed with rest of params
    serial = []
    for i in range(1, 9):
        num = random.randint(1, 9)
        letter = random.choice(string.ascii_letters).capitalize()
        complete = f"{num}{letter}"
        serial.append(complete)
    pokemon['id'] = ''.join(serial)

    #Print Pokemon perms to channel for records - Webhook
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url('https://discord.com/api/webhooks/1237465290636263514/6hnjg9TAi0ec0LBhdlii8KNxptcj4E1RZ0unN7WMKUeAyiqndxiPMxAHhtJaEBFi50Wk', session=session)
        embed = discord.Embed(
            title="A NPC Pokemon was generated!",
            description=f"\N{SMALL BLUE DIAMOND}\nID: ``{self.author.id}``\nSerial: {pokemon['id']}\n```{pokemon}```"
        )
        await webhook.send(embed=embed)

    #Print Pokemon perms to channel for records - Message
    #await self.bot.get_partial_messageable(1130947230279405658).send(
        #f"\N{SMALL BLUE DIAMOND}- A Pokemon has been generated!\nID: ``{self.author.id}``\nSerial: {pokemon['id']}\n```{pokemon}```"
    #)

    return pokemon

trainers = [
    'Picnicker Ivelisse',
    'Psychic Jordan',
    'Master Trainer Alex',
    'Lass Madeline',
    'Youngster Joey',
    'Fisher Walter',
    'Blackbelt Lex',
    'Hiker Bob',
    'Swimmer Bri',
    'Ace Trainer Liz'
]