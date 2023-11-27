import asyncio
import math
import asyncpg
import random
import time

from discord.ext import commands
from typing import List, Union
from datetime import datetime, timedelta
from mewcogs.json_files import *
from mewcogs.pokemon_list import *
from mewcogs.pokemon_list import _
from mewutils.misc import get_emoji, pagify, MenuView, AsyncIter
from dataclasses import dataclass
from collections import defaultdict


async def get_child(ctx, father, mother, shiny=False):
    # Nature
    natures = []
    if father.held_item == "everstone":
        natures.append(father.nature)
    if mother.held_item == "everstone":
        natures.append(mother.nature)
    if natures:
        nature = random.choice(natures)
    else:
        nature = random.choice(natlist)

    # IVs
    # 29/30 chance to have a max default stat of 22
    # 01/30 chance to have a max default stat of 25
    thold = 22 if random.randint(0, 29) else 25
    # build default stats based on threshold
    hp = random.randint(0, thold)
    attack = random.randint(0, thold)
    defense = random.randint(0, thold)
    specialattack = random.randint(0, thold)
    specialdefense = random.randint(0, thold)
    speed = random.randint(0, thold)

    identifier = mother.name.lower()

    pokemon_pfile = await ctx.bot.db[1].pfile.find_one({"identifier": identifier})
    if pokemon_pfile is None:
        ctx.bot.logger.warning(f"No PFILE exists for PARENT {identifier}")
        return None, None

    # Recursively find the base evo
    while pokemon_pfile["evolves_from_species_id"]:
        parent = pokemon_pfile["identifier"]
        pokemon_pfile = await ctx.bot.db[1].pfile.find_one(
            {"id": pokemon_pfile["evolves_from_species_id"]}
        )
        if pokemon_pfile is None:
            ctx.bot.logger.warning(
                f"No PFILE exists for evolves_from_species_id of {parent}"
            )
            return None, None

    # Override for possibly the stupidest edge case ever, manaphy produces phione eggs, but phione does not evolve into manaphy
    if pokemon_pfile["identifier"] == "manaphy":
        pokemon_pfile = await ctx.bot.db[1].pfile.find_one({"identifier": "phione"})

    name = pokemon_pfile["identifier"]
    gender_rate = pokemon_pfile["gender_rate"]
    id = pokemon_pfile["id"]
    counter = pokemon_pfile["hatch_counter"] * 2

    ab_ids = []
    async for record in ctx.bot.db[1].poke_abilities.find({"pokemon_id": id}):
        ab_ids.append(record["ability_id"])

    egg_groups = (await ctx.bot.db[1].egg_groups.find_one({"species_id": id}))[
        "egg_groups"
    ]

    # two stats are passed from parents to their child
    # both parents pass one stat
    stats = ["hp", "attack", "defense", "spatk", "spdef", "speed"]
    parents = (father, mother)
    inherited_stats = random.sample(stats, 2)
    for idx, stat in enumerate(inherited_stats):
        if stat == "hp":
            hp = parents[idx].hp
        if stat == "attack":
            attack = parents[idx].attack
        if stat == "defense":
            defense = parents[idx].defense
        if stat == "spatk":
            specialattack = parents[idx].spatk
        if stat == "spdef":
            specialdefense = parents[idx].spdef
        if stat == "speed":
            speed = parents[idx].speed

    abilitated = [ab in mother.ab_ids for ab in ab_ids]
    if True in abilitated:
        try:
            ab_id = ab_ids.index(random.choice(mother.ab_ids))
        except:
            ab_id = ab_ids[0]
    else:
        try:
            ab_id = ab_ids.index(random.choice(ab_ids))
        except:
            ab_id = ab_ids[0]

    knotted = True
    if mother.held_item == "ultra_destiny_knot":
        parent = mother
        num = 3 if random.randint(0, 9) else 4
    elif father.held_item == "ultra_destiny_knot":
        parent = father
        num = 3 if random.randint(0, 9) else 4
    elif mother.held_item == "destiny_knot":
        parent = mother
        num = 1 if random.randint(0, 2) else 2
    elif father.held_item == "destiny_knot":
        parent = father
        num = 1 if random.randint(0, 2) else 2
    else:
        knotted = False
    if knotted:
        stats = ["hp", "attack", "defense", "spatk", "spdef", "speed"]
        new_stats = random.sample(stats, num)
        if "hp" in new_stats:
            hp = parent.hp
        if "attack" in new_stats:
            attack = parent.attack
        if "defense" in new_stats:
            defense = parent.defense
        if "spatk" in new_stats:
            specialattack = parent.spatk
        if "spdef" in new_stats:
            specialdefense = parent.spdef
        if "speed" in new_stats:
            speed = parent.speed

    steps = (counter * 257) // 20

    # Gender
    if "idoran-" in name:
        gender = name[-2:]
    elif name.lower() == "illumise":
        gender = "-f"
    elif name.lower() in ("volbeat", "tauros-paldea"):
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

    p = Pokemon(
        name.capitalize(),
        gender,
        hp,
        attack,
        defense,
        specialattack,
        specialdefense,
        speed,
        1,
        shiny,
        "None",
        0,
        ab_id,
        ab_ids,
        egg_groups,
        nature,
        0,
    )
    return p, steps


async def get_parent(ctx, challenger):
    pn = challenger["pokname"]
    hp = challenger["hpiv"]
    attack = challenger["atkiv"]
    defense = challenger["defiv"]
    specialattack = challenger["spatkiv"]
    specialdefense = challenger["spdefiv"]
    speed = challenger["speediv"]
    hpev = challenger["hpev"]
    atkev = challenger["atkev"]
    defev = challenger["defev"]
    spaev = challenger["spatkev"]
    spdev = challenger["spdefev"]
    speev = challenger["speedev"]
    plevel = challenger["pokelevel"]
    shiny = challenger["shiny"]
    id = challenger["id"]
    hitem = challenger["hitem"]
    happiness = challenger["happiness"]
    ab_index = challenger["ability_index"]

    pokemon_pfile = await ctx.bot.db[1].pfile.find_one({"identifier": pn.lower()})
    if not pokemon_pfile and "alola" in pn:
        pokemon_pfile = await ctx.bot.db[1].pfile.find_one(
            {"identifier": pn.lower()[:-6]}
        )

    if not pokemon_pfile:
        ctx.bot.logger.warning("No PFILE exists for %s " % pn)
        return None
    ab_ids = []

    form_info = await ctx.bot.db[1].forms.find_one({"identifier": pn.lower()})

    if form_info is None:
        ctx.bot.logger.warning(f'Pokemon "{pn}" does not exist in mongo forms.')

    stats = (
        await ctx.bot.db[1].pokemon_stats.find_one(
            {"pokemon_id": form_info["pokemon_id"]}
        )
    )["stats"]

    pokemonSpeed = stats[5]
    pokemonSpd = stats[4]
    pokemonSpa = stats[3]
    pokemonDef = stats[2]
    pokemonAtk = stats[1]
    pokemonHp = stats[0]
    evo_chain = pokemon_pfile["evolution_chain_id"]
    name = (
        await ctx.bot.db[1].pfile.find_one(
            {"evolution_chain_id": pokemon_pfile["evolution_chain_id"]}
        )
    )["identifier"]

    name_pfile = await ctx.bot.db[1].pfile.find_one({"identifier": name})
    gender_rate = name_pfile["gender_rate"]
    id = name_pfile["id"]
    counter = name_pfile["hatch_counter"] * 4
    capture_rate = name_pfile["capture_rate"]

    async for record in ctx.bot.db[1].poke_abilities.find({"pokemon_id": id}):
        ab_ids.append(record["ability_id"])

    try:
        ab_id = ab_ids[ab_index]
    except:
        ab_id = ab_ids[0]

    try:
        egg_groups = (
            await ctx.bot.db[1].egg_groups.find_one(
                {"species_id": form_info["pokemon_id"]}
            )
        )["egg_groups"]
    except:
        await ctx.bot.db[1].egg_groups.insert_one(
            {"species_id": form_info["pokemon_id"], "egg_groups": [1]}
        )
        egg_groups = (
            await ctx.bot.db[1].egg_groups.find_one(
                {"species_id": form_info["pokemon_id"]}
            )
        )["egg_groups"]
        await ctx.send("Default egg group used.")

    try:
        eid = [t["id"] for t in PKIDS if t["evolves_from_species_id"] == pkid[0]][0]
    except:
        eid = None
    happiness = 0

    p = Pokemon(
        pn.capitalize(),
        challenger["gender"],
        hp,
        attack,
        defense,
        specialattack,
        specialdefense,
        speed,
        plevel,
        shiny,
        hitem,
        happiness,
        ab_id,
        ab_ids,
        egg_groups,
        challenger["nature"],
        capture_rate,
    )

    return p


def get_insert_query(ctx, poke, counter, mother, is_shadow):
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
        counter,
        poke.name,
        poke.gender,
        ctx.author.id,
        poke.shiny,
        skin,
    )
    return query2, args


def get_mother_query(mother_id, owner):
    hour = datetime.now().hour
    hour += 6
    query = """
    INSERT INTO mothers(pokemon_id, owner)
    VALUES ($1, $2)
    """
    args = mother_id, owner
    return query, args


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
    egg_groups: list
    nature: str
    capture_rate: int

    def is_a_form(self):
        return is_formed(self.name)

    def is_a_regional_form(self):
        return any(
            self.name.endswith(form) for form in ["alola", "galar", "hisui", "paldea"]
        )


class RedoBreedView(discord.ui.View):
    def __init__(self, ctx, cog, male, female):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.cog = cog
        self.male = male
        self.female = female
        self.message = None

    @discord.ui.button(label="Redo breed", style=discord.ButtonStyle.secondary)
    async def redo(self, interaction, button):
        await interaction.response.defer()
        self.ctx._created_at = time.time()
        self.ctx._interaction = interaction
        await self.cog.breed.callback(
            self.cog, self.ctx, self.male, females=self.female
        )
        
    @discord.ui.button(label="Cancel breed", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction, button):
        await interaction.response.defer()
        self.ctx._created_at = time.time()
        self.ctx._interaction = interaction
        self.ctx.command.cancel = True
        await self.message.edit(embed=make_embed(title=f"Auto Breeding Canceled"), view=None)
        return

    #@discord.ui.button(
        #label="Auto redo until success", style=discord.ButtonStyle.primary
    #)
    async def auto(self, interaction, button):
        await interaction.response.defer()
        if self.cog.auto_redo[self.ctx.author.id] is not None:
            view = CancelRedoView(self.ctx, self.cog)
            message = await interaction.followup.send(
                "You already have an active auto-breed. Cancel that one first!",
                view=view,
                ephemeral=True,
            )
            view.message = message
            return

        patreon = await self.ctx.bot.patreon_tier(self.ctx.author.id)
        if patreon not in ("Crystal Tier", "Silver Tier"):
            await interaction.followup.send(
                "This feature is only available to Silver patreons and above! See `/donate` to become a patreon.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "I will attempt to breed these pokes until the breed is successful!",
            ephemeral=True,
        )
        await self.ctx.send([self.male, self.female])
        self.cog.auto_redo[self.ctx.author.id] = [self.male, self.female]
        await asyncio.sleep(37)
        if self.cog.auto_redo[self.ctx.author.id] == [self.male, self.female]:
            await self.cog.breed.callback(
                self.cog, self.ctx, self.male, females=str(self.female) + "auto"
            )

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content="You are not allowed to interact with this button.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        if not self.message:
            return
        try:
            await self.message.edit(view=None)
        except discord.NotFound:
            pass

    async def on_error(self, interaction, error, item):
        await self.ctx.bot.misc.log_error(self.ctx, error)


class CancelRedoView(discord.ui.View):
    def __init__(self, ctx, cog):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.cog = cog
        self.message = None

    @discord.ui.button(label="Cancel auto breed", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction, button):
        self.cog.auto_redo[self.ctx.author.id] = None
        await interaction.response.send_message(
            "I will no longer automatically attempt to breed these pokes.",
            ephemeral=True,
        )

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content="You are not allowed to interact with this button.",
                ephemeral=True,
            )
            return False
        return True

    async def on_error(self, interaction, error, item):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def on_timeout(self):
        if not self.message:
            return
        try:
            await self.message.edit(view=None)
        except discord.NotFound:
            pass


class Breeding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_task = asyncio.create_task(self.initialize())
        self.auto_redo = defaultdict(lambda: None)  # user id: args

    async def initialize(self):
        # This is to make sure the breedcooldowns dict exists before we access in the cog check
        await self.bot.redis_manager.redis.execute(
            "HMSET", "breedcooldowns", "examplekey", "examplevalue"
        )
        
    async def get_female_max(self, user):
        patreon_status = await self.bot.patreon_tier(user)
        if patreon_status in ("Crystal Tier", "Sapphire Tier"):
            limit = 150
        elif patreon_status == "Silver Tier":
            limit = 45
        elif patreon_status == "Yellow Tier":
            limit = 30
        elif patreon_status == "Red Tier" and random.randint(0, 1):
            limit = 15
        else:
            limit = 10
        return limit

    async def reset_cooldown(self, id_):
        await self.bot.redis_manager.redis.execute(
            "HMSET", "breedcooldowns", str(id_), "0"
        )
        self.auto_redo[id_] = None

    @commands.hybrid_command()
    @discord.app_commands.describe(
        male="The Male Pokémon to be bred.",
        females="The list of Female Pokémon to be bred.",
    )
    async def breed(self, ctx, male: int, *, females):
        """Breeds two Pokémon - Male & Female"""
        if type(females) == str:
            auto = females.endswith("auto")
            if auto:
                females = females[:-4]
            females_list = list(
                dict.fromkeys([int(x) for x in females.split(" ") if x.isdigit()])
            )

        elif type(females) == list:
            auto = females[-1] == "auto"
            if auto:
                females.pop(-1)  # ngl idk any better way to do this easy lol
            females_list = females

        elif type(females) == int:
            auto = False
            females_list = [females]

        #TODO: Add Patreon specific rewards    
        #get_female_max uses get_patreon which requires
        #specific return int value per tier
        #if len(females_list) > self.get_female_max(ctx.author.id):
            #await ctx.send(f"You can not breed more than {self.get_female_max(ctx.author.id)} females.")
            #return
        #TEMP:
        limit = await self.get_female_max(ctx.author.id)
        if len(females_list) > limit:
            await ctx.send(f"You can not queue more than {limit} Female IDs.\nPatreon increases your limit, `/donate`")
            return

        for female in females_list:
            ctx.command.cancel = False
            # Remove this female from the list of females - "unorthodoxly"
            # females = females.replace(str(female), "")
            # await ctx.send(f"Breeding {female}")
            try:
                male = int(male)
                female = int(female)
            except ValueError:
                await ctx.send("You need to provide two pokemon id numbers.")
                return
            if male > 2147483647 or female > 2147483647:
                await ctx.send("You do not have that many pokemon!")
                return
            breed_reset = (
                await ctx.bot.redis_manager.redis.execute(
                    "HMGET", "breedcooldowns", str(ctx.author.id)
                )
            )[0]

            if breed_reset is None:
                breed_reset = 0
            else:
                breed_reset = float(breed_reset.decode("utf-8"))

            if breed_reset > time.time():
                reset_in = breed_reset - time.time()
                cooldown = f"{round(reset_in)}s"
                await ctx.send(f"Command on cooldown for {cooldown}")
                return
            await ctx.bot.redis_manager.redis.execute(
                "HMSET", "breedcooldowns", str(ctx.author.id), str(time.time() + 35)
            )
            if male == female:
                await ctx.send("You can not breed the same Pokemon!")
                await self.reset_cooldown(ctx.author.id)
                return
            father, mother = male, female
            async with ctx.bot.db[0].acquire() as pconn:
                pokes = await pconn.fetchrow(
                    "SELECT pokes, daycarelimit, chain FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
                multipliers = await pconn.fetchrow(
                    "SELECT shiny_multiplier, breeding_multiplier FROM account_bound WHERE u_id = $1",
                    ctx.author.id,
                )
                if multipliers is None:
                    shiny_multiplier = 0
                    breedmulti = 0
                else:
                    shiny_multiplier = multipliers["shiny_multiplier"]
                    breedmulti = multipliers["breeding_multiplier"]

                # Check if not existing
                if shiny_multiplier is None:
                    shiny_multiplier = 0
                if breedmulti is None:
                    breedmulti = 0

                if pokes is None:
                    await ctx.send("You have not started!\nStart with `/start` first.")
                    return
                s_threshold = round(8000 - 8000 * (shiny_multiplier / 100))
                is_shiny = random.choice([False for i in range(s_threshold)] + [True])

                dlimit = pokes["daycarelimit"]
                chain = pokes["chain"]
                pokes = pokes["pokes"]
                daycared = await pconn.fetchval(
                    "SELECT count(*) FROM pokes WHERE id = ANY ($1) AND pokname = 'Egg'",
                    pokes,
                )
                if daycared > dlimit:
                    await ctx.send("You already have enough Pokemon in the Daycare!")
                    await self.reset_cooldown(ctx.author.id)
                    return
                father_details = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT pokes[$1] FROM users WHERE u_id = $2)",
                    father,
                    ctx.author.id,
                )
                mother_details = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT pokes[$1] FROM users WHERE u_id = $2)",
                    mother,
                    ctx.author.id,
                )
                if father_details is None or mother_details is None:
                    await ctx.send("You do not have that many pokemon!")
                    await self.reset_cooldown(ctx.author.id)
                    return
                if "Egg" in (father_details["pokname"], mother_details["pokname"]):
                    await ctx.send("You cannot breed an egg!")
                    await self.reset_cooldown(ctx.author.id)
                    return

                # Dittos cannot breed
                if (
                    mother_details["pokname"] == "Ditto"
                    and father_details["pokname"] == "Ditto"
                ):
                    await ctx.send("You cannot breed two dittos!")
                    await self.reset_cooldown(ctx.author.id)
                    return

                # Ditto is always the father, since the mother passes the pokname, and ditto cannot pass the pokname
                if mother_details["pokname"] == "Ditto":
                    mother_details, father_details = father_details, mother_details

                # Properly order non-dittoed pokemon
                if father_details["pokname"] != "Ditto":
                    if mother_details["gender"] == "-m":
                        mother_details, father_details = father_details, mother_details
                    if (
                        mother_details["gender"] != "-f"
                        or father_details["gender"] != "-m"
                    ):
                        await ctx.send(
                            "You may breed one male and one or more female pokemon, or breed with a ditto."
                        )
                        await self.reset_cooldown(ctx.author.id)
                        return

                cooldowned = await pconn.fetchval(
                    "SELECT pokemon_id FROM mothers WHERE pokemon_id = $1",
                    mother_details["id"],
                )
                if cooldowned:
                    await ctx.send(
                        f"Your {mother_details['pokname']} is currently on cooldown... See `/f p args:cooldown`."
                    )
                    await self.reset_cooldown(ctx.author.id)
                    return
            father = await get_parent(ctx, father_details)
            if father is None:
                await ctx.send(
                    f"You can not breed a {father_details['pokname']}! You might need to `/deform` it first."
                )
                await self.reset_cooldown(ctx.author.id)
                return
            mother = await get_parent(ctx, mother_details)
            if mother is None:
                await ctx.send(
                    f"You can not breed a {mother_details['pokname']}! You might need to `/deform` it first."
                )
                await self.reset_cooldown(ctx.author.id)
                return
            if 15 in father.egg_groups:
                await ctx.send("You can not breed undiscovered egg groups!")
                await self.reset_cooldown(ctx.author.id)
                return
            if 15 in mother.egg_groups:
                await ctx.send("You can not breed undiscovered egg groups!")
                await self.reset_cooldown(ctx.author.id)
                return
            father_total_iv = (
                father.hp
                + father.attack
                + father.defense
                + father.spatk
                + father.spdef
                + father.speed
            )
            mother_total_iv = (
                mother.hp
                + mother.attack
                + mother.defense
                + mother.spatk
                + mother.spdef
                + mother.speed
            )

            # The code below prevents hexas from being bred. It is here *for now* due to the snowballing effect of breeding hexas.
            if 186 in (father_total_iv, mother_total_iv):
                await ctx.send("You cannot breed 100% iv pokemon!")
                await self.reset_cooldown(ctx.author.id)
                return

            breedable = any((id in father.egg_groups for id in mother.egg_groups))
            dittoed = "Ditto" in (father.name.capitalize(), mother.name.capitalize())
            manaphied = any(
                (
                    "Manaphy" in (father.name, mother.name),
                    "Phione" in (father.name, mother.name),
                )
            )
            manaphied = manaphied and dittoed
            conditions = (manaphied, breedable, dittoed)

            if not any(conditions):
                await ctx.send("These Two Pokemon are not breedable!")
                await self.reset_cooldown(ctx.author.id)
                return

            child, counter = await get_child(ctx, father, mother, is_shiny)
            if child is None:
                await ctx.send(
                    f"You can not breed a {mother_details['pokname']}! You might need to `/deform` it first."
                )
                await self.reset_cooldown(ctx.author.id)
                return

            if father_total_iv < 40:
                father_total_iv = 120
            if mother_total_iv < 40:
                mother_total_iv = 120
            chance = (min(100, father.capture_rate) + min(100, mother.capture_rate)) / (
                (father_total_iv + mother_total_iv) * 3
            )
            inc = (breedmulti / 50.0) + 1.0  # * 1.0 - 2.0
            chance *= inc
            if ctx.bot.premium_server(ctx.guild.id):
                chance *= 1.05
            success = random.choices([True, False], weights=(chance, 1 - chance))[0]
            chance_message = f"Chance of success: {chance * 100:.2f}% | {ctx.author}"

            # Failed attempt
            if not success:
                embed = discord.Embed(
                    title=f"Breeding Attempt Failed!",
                    description=f"Factors affecting this include Parent Catch Rate and IV %\nYou can breed again: <t:{int(time.time()) + 36}:R>",
                ).set_footer(text=chance_message)
                if auto:
                    view = CancelRedoView(ctx, self)
                else:
                    view = RedoBreedView(ctx, self, male, female)
                message = await ctx.send(embed=embed, view=view, ephemeral=True)
                view.message = message
                await asyncio.sleep(37)
                
                if ctx.command.cancel:
                    return
                
                embed = discord.Embed(
                    title="Breeding Attempt Failed!",
                    description=f"Factors affecting this include Parent Catch Rate and IV %\nYou can breed again: Now!",
                ).set_footer(text=chance_message)
                try:
                    await message.edit(embed=embed)
                except discord.NotFound:
                    pass
                if auto and self.auto_redo[ctx.author.id] == [male, female]:
                    return await self.breed.callback(
                        self, ctx, male, females=str(female) + "auto"
                    )

            # Got an egg
            else:

                self.auto_redo[ctx.author.id] = None

                patreon_status = await ctx.bot.patreon_tier(ctx.author.id)

                # Reduce Cgrubb's base step count for testing
                # Test will be for reducing overall step count in the bot.
                if ctx.author.id == (366319068476866570, 334155028170407949):
                    # Let's start with a flat 15% decrease
                    counter = counter - round(counter * (10 / 100))

                if patreon_status in ("Crystal Tier", "Sapphire Tier"):
                    counter = counter - round(counter * (50 / 100))
                elif patreon_status == "Silver Tier":
                    counter = counter - round(counter * (30 / 100))
                elif patreon_status == "Yellow Tier":
                    counter = counter - round(counter * (20 / 100))
                elif patreon_status == "Red Tier" and random.randint(0, 1):
                    counter = counter - round(counter * (20 / 100))

                is_shadow = False
                if not child.shiny:
                    is_shadow = await ctx.bot.commondb.shadow_hunt_check(
                        ctx.author.id, child.name
                    )
                if is_shadow:
                    await ctx.bot.get_partial_messageable(998341289164689459).send(
                        f"`Shadow through Breeding: {ctx.author.id} - {child.name}`"
                    )
                emoji = get_emoji(
                    shiny=child.shiny,
                    skin="shadow" if is_shadow else None,
                )

                query, args = get_insert_query(ctx, child, counter, mother, is_shadow)
                mother_query, mother_args = get_mother_query(
                    mother_details["id"], ctx.author.id
                )
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(mother_query, *mother_args)
                    pokeid = await pconn.fetchval(query, *args)
                    # a = await pconn.fetchval("SELECT currval('pokes_id_seq');")
                    await pconn.execute(
                        "UPDATE users SET pokes = array_append(pokes, $1) WHERE u_id = $2",
                        pokeid,
                        ctx.author.id,
                    )
                name = mother.name
                ivsum = (
                    child.attack
                    + child.defense
                    + child.spatk
                    + child.spdef
                    + child.speed
                    + child.hp
                )
                # TODO: achievement code

                ivpercent = round((ivsum / 186) * 100, 2)
                e = make_embed(title=f"Your {emoji}{name} Egg ({ivpercent}% iv)")
                e.description = f"It will hatch after {counter} messages!"
                embed = discord.Embed(
                    title=f"{ctx.author.name}'s {emoji}{name.capitalize()} ({ivpercent}% IV) Egg!",
                    description="It's been automatically added to your Pokemon list.",
                    color=0x00FF00,
                )
                embed.add_field(
                    name="Egg Details",
                    value=f"You received a {emoji}{name.capitalize()} Egg!\nIt'll hatch after {counter} messages.",
                    inline=True,
                )
                embed.add_field(
                    name="Cooldowns",
                    value=f"{mother_details['pokname'].title()} will be on a 6hr cooldown\nYou can breed again in **<t:{int(time.time()) + 36}:R>**",
                    inline=True,
                )
                if is_shadow:
                    embed.add_field(
                        name="Shadow Details",
                        value=f"This Shadow took {chain} attempts! WOW!",
                        inline=True,
                    )
                embed.set_image(
                    url="https://mewbot.xyz/eastereggs.png"
                )
                embed.set_footer(text=chance_message)
                
                async def button1_callback(interaction: discord.Interaction):
                    if interaction.user == ctx.author:
                        ctx.command.cancel = True
                        await interaction.message.edit(embed=make_embed(title=f"Auto Breeding Canceled"))
                        return

                button1 = discord.ui.Button(label="Cancel Next Breed", custom_id="button1")
                button1.callback = button1_callback

                view = discord.ui.View(timeout=15)
                view.add_item(button1)
                try:
                    if auto:
                        message = await ctx.send(ctx.author.mention, embed=embed, view=view)
                    else:
                        message = await ctx.send(embed=embed, view=view)
                except discord.NotFound:
                    pass
                self.bot.dispatch("poke_breed", ctx.channel, ctx.author)
                
                try:
                    interaction: discord.Interaction = await ctx.bot.wait_for(
                        "button_click",
                        check=lambda i: i.message.id == message.id and i.user.id == ctx.author.id,
                        timeout=120
                    )
                    await message.edit(view=None)
                except:
                    await message.edit(view=None)
                    pass
                
                if ctx.command.cancel:
                    print("Canceled cmd")
                    return
                    
                # Dispatches an event that a poke was bred.
                # on_poke_breed(self, channel, user)
                # self.bot.dispatch("poke_breed", ctx.channel, ctx.author)

                # embed = discord.Embed(
                #     title=f"{ctx.author.name}'s {emoji}{name.capitalize()} ({ivpercent}% IV) Egg!",
                #     description="It's been automatically added to your Pokemon list.",
                #     color=0x00FF00,
                # )
                # embed.add_field(
                #     name="Egg Details",
                #     value=f"You received a {emoji}{name.capitalize()} Egg!\nIt'll hatch after {counter} messages.",
                #     inline=True,
                # )
                # embed.add_field(
                #     name="Cooldowns",
                #     value=f"{mother_details['pokname'].title()} will be on a 6hr cooldown\nYou can breed again **Now**",
                #     inline=True,
                # )
                # if is_shadow:
                #     embed.add_field(
                #         name="Shadow Details",
                #         value=f"This Shadow took {chain} attempts! WOW!",
                #         inline=True,
                #     )
                # embed.set_image(
                #     url="https://mewbot.xyz/eastereggs.png"
                # )
                # embed.set_footer(text=chance_message)
                
                # async def button1_callback(interaction: discord.Interaction):
                #     if interaction.user == ctx.author:
                #         return

                # button1 = discord.ui.Button(label="Cancel Next Breed", custom_id="button1")
                # button1.callback = button1_callback

                # view = discord.ui.View(timeout=15)
                # view.add_item(button1)
                # try:
                #     await message.edit(embed=e, view=view)
                # except discord.NotFound:
                #     pass

                # interaction: discord.Interaction = await ctx.bot.wait_for(
                #     "button_click",
                #     check=lambda i: i.message.id == message.id and i.user.id == ctx.author.id,
                #     timeout=36
                # )
                

    @commands.hybrid_command()
    @discord.app_commands.describe(
        pokemon="The Pokémon to check compatibility.",
        filter_args="Extra arguments to filter - see /filter for more.",
    )
    async def breedswith(self, ctx, pokemon: int, filter_args: str = None):
        """Runs a version of filter that only shows all compatible Pokémon for breeding."""
        async with ctx.bot.db[0].acquire() as pconn:
            poke = await pconn.fetchval(
                "SELECT pokes[$1] FROM users WHERE u_id = $2", pokemon, ctx.author.id
            )
            if poke is None:
                await ctx.send("That pokemon does not exist!")
                return
            details = await pconn.fetchrow(
                "SELECT pokname, gender FROM pokes WHERE id = $1", poke
            )
        if details["pokname"].lower() == "ditto":
            await ctx.send("Dittos can breed with any pokemon except for other dittos.")
            return
        if details["gender"] == "-x":
            await ctx.send("Genderless pokemon can only breed with ditto.")
            return
        elif details["gender"] == "-f":
            gender = "male"
        else:
            gender = "female"
        form_info = await ctx.bot.db[1].forms.find_one(
            {"identifier": details["pokname"].lower()}
        )
        egg_groups = await ctx.bot.db[1].egg_groups.find_one(
            {"species_id": form_info["pokemon_id"]}
        )
        if egg_groups is None:
            await ctx.send("That pokemon cannot be bred! It may be formed.")
            return
        egg_groups = egg_groups["egg_groups"]
        if 15 in egg_groups:
            await ctx.send("Pokemon in the undiscovered egg group cannot breed!")
            return
        egg_groups_str = " ".join(
            [
                (await ctx.bot.db[1].egg_groups_info.find_one({"id": egg_group_id}))[
                    "identifier"
                ]
                for egg_group_id in egg_groups
            ]
        )
        args = f"(name ditto | (egg {egg_groups_str} & {gender})) & !cooldown"
        if filter_args is not None:
            args = f"({args}) & ({filter_args})"

        cog = ctx.bot.get_cog("Filter")
        if not cog:
            await ctx.send("That command cannot be used right now. Try again later.")
            return
        await cog.f.get_command("p").callback(cog, ctx, args=args)

    # @commands.hybrid_command()
    async def daycare(self, ctx):
        await ctx.send(
            "This command is deprecated, you should use `/f p args:name egg` instead. "
            "It has the same functionality, but with a fresh output and the ability to use additional filters.\n"
            "Running that for you now..."
        )
        await asyncio.sleep(3)
        c = ctx.bot.get_cog("Filter")
        if c is None:
            return
        await c.f.get_command("p").callback(c, ctx, args="name egg")
        return


async def setup(bot):
    await bot.add_cog(Breeding(bot))
