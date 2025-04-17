import random
import discord

from mewcogs.pokemon_list import natlist
from mewutils.misc import get_emoji
from mewcore.items import *
from datetime import datetime, time
from zoneinfo import ZoneInfo


class UserNotStartedError(Exception):
    """
    Generic exception that is raised when a DB
    util is used on a user who has not started.
    """

    pass


class Pokemon:
    """Dataclass to hold information about a created pokemon."""

    def __init__(self, id, gender, iv_sum, emoji):
        self.id = id
        self.gender = gender
        self.iv_sum = iv_sum
        self.emoji = emoji


class Item:
    """Dataclass to hold info about an added item"""

    def __init__(self, item_name, quantity):
        self.item_name = item_name
        self.quantity = quantity


class CommonDB:
    def __init__(self, bot):
        self.bot = bot
        self.ALPHA_POKEMON = [
            "Infernape",
            "Porygon-z",
            "Iron-thorns",
            "Flygon",
            "Mimikyu",
            "Guzzlord", 
            "Spinda"
        ]

        self.ALL_ALPHA_POKEMON = [
            "Infernape",
            "Porygon-z",
            "Iron-thorns",
            "Flygon",
            "Mimikyu",
            "Guzzlord",
            "Starmie",
            "Salamence",
            "Blacephalon",
            "Lunatone",
            "Iron-hands",
            "Altaria",
            "Zeraora",
            "Vikavolt",
            "Venusaur",
            "Krookodile",
            "Sceptile",
            "Falinks",
            "Talonflame",
            "Butterfree",
            "Heatran",
            "Regigigas",
            "Regirock",
            "Regice",
            "Registeel",
            "Arceus",
            "Darkrai",
            "Diancie",
            "Volcanion",
            "Deoxys",
            "Latios",
            "Mewtwo",
            "Solgaleo",
            "Ampharos",
            "Raticate-alola",
            "Tinkaton",
            "Darkrai",
            "Uxie",
            "Diancie",
            "Mewtwo", "Gardevoir",
            "Rayquaza",
            "Leafeon",
            "Hydreigon",
            "Azumarill",
            "Groudon",
            "Dhelmise",
            "Electivire",
            "Magmortar",
            "Rhyperior",
            "Kyogre",
            "Cobalion",
            "Camerupt",
            "Absol",
            "Spiritomb",
            "Manectric",
            "Greninja",
            "Rabsca",
            "Lokix",
            "Koraidon",
            "Dialga",
            "Necrozma",
            "Ninetales",
            "Scovillain",
            "Politoed",
            "Heatran",
            "Latios",
            "Solgaleo",
            "Beedrill",
            "Heracross",
            "Manaphy",
            "Salamence",
            "Gallade",
            "Gogoat",
            "Pyroar",
            "Aegislash",
            "Braviary-hisui",
            "Druddigon",
            "Raikou",
            "Zacian",
            "Celebi",
            "Lugia",
            "Bellossom",
            "Vileplume",
            "Cobalion",
            "Pidgeot",
            "Corviknight",
            "Slaking",
            "Ceruledge",
            "Breloom",
            "Cloyster",
            "Cinderace",
            "Poliwrath",
            "Meloetta",
            "Bibarel",
            "Blaziken",
            "Blastoise",
            "Drapion",
            "Jirachi",
            "Floatzel",
            "Lucario",
            "Audino",
            "Thundurus",
            "Swampert",
            "Lycanroc",
            "Melmetal",
            "Iron-jugulis",
            "Terrakion",
            "Walking-wake",
            "Glastrier",
            "Samurott-hisui", 
            "Spinda", 
        ]
        self.ALPHA_MOVESETS = {
            "Infernape": ["mountain-gale", "tackle", "tackle", "tackle"],
            "Porygon-z": ["blood moon", "tackle", "tackle", "tackle"],
            "Iron-thorns": ["shift-gear", "tackle", "tackle", "tackle"],
            "Flygon": ["victory-dance", "tackle", "tackle", "tackle"],
            "Mimikyu": ["spectral-thief", "tackle", "tackle", "tackle"],
            "Guzzlord": ["comeuppance", "tackle", "tackle", "tackle"],
            "Spinda": ["v-create", "tackle", "tackle", "tackle"],
            "Starmie": ["prismatic-laser", "tackle", "tackle", "tackle"],
            "Salamence": ["dragon-darts", "tackle", "tackle", "tackle"],
            "Blacephalon": ["astral-barrage", "tackle", "tackle", "tackle"],
            "Lunatone": ["geomancy", "tackle", "tackle", "tackle"],
            "Iron-hands": ["plasma-fists", "tackle", "tackle", "tackle"],
            "Altaria": ["calm-mind", "tackle", "tackle", "tackle"],
            "Zeraora": ["ice-punch", "tackle", "tackle", "tackle"],
            "Melmetal": ["jet-punch", "tackle", "tackle", "tackle"],  # New entry
            "Iron-jugulis": ["nasty-plot", "tackle", "tackle", "tackle"],  # New entry
            "Terrakion": ["diamond-storm", "tackle", "tackle", "tackle"],  # New entry
            "Walking-wake": ["clanging-scales", "tackle", "tackle", "tackle"],  # New entry
            "Glastrier": ["ice-shard", "tackle", "tackle", "tackle"],  # New entry
            "Samurott-hisui": ["bitter-blade", "tackle", "tackle", "tackle"],  # New entry
            "Floatzel": ["surging-strikes", "tackle", "tackle", "tackle"],
            "Lucario": ["glacial-lance", "tackle", "tackle", "tackle"],
            "Audino": ["soft-boiled", "tackle", "tackle", "tackle"],
            "Thundurus": ["hurricane", "tackle", "tackle", "tackle"],
            "Swampert": ["slack-off", "tackle", "tackle", "tackle"],
            "Lycanroc": ["headlong-rush", "tackle", "tackle", "tackle"],
            "Vikavolt": ["thunderclap", "tackle", "tackle", "tackle"],
            "Venusaur": ["matcha-gotcha", "tackle", "tackle", "tackle"],
            "Krookodile": ["dragon-dance", "tackle", "tackle", "tackle"],
            "Sceptile": ["draco-meteor", "tackle", "tackle", "tackle"],
            "Falinks": ["power-trip", "tackle", "tackle", "tackle"],
            "Talonflame": ["dragon-ascent", "tackle", "tackle", "tackle"],
            "Butterfree": ["focus-blast", "tackle", "tackle", "tackle"],
            "Golurk": ["mach-punch", "tackle", "tackle", "tackle"],
            "Snorlax": ["slack-off", "tackle", "tackle", "tackle"],
            "Banette": ["spectral-thief", "tackle", "tackle", "tackle"],
            "Aerodactyl": ["brave-bird", "tackle", "tackle", "tackle"],
            "Torterra": ["shell-smash", "tackle", "tackle", "tackle"],
            "Goodra": ["core-enforcer", "tackle", "tackle", "tackle"],
            "Heatran": ["meteor-beam", "tackle", "tackle", "tackle"],
            "Regigigas": ["power-swap", "tackle", "tackle", "tackle"],
            "Regirock": ["shore-up", "tackle", "tackle", "tackle"],
            "Regice": ["freeze-dry", "tackle", "tackle", "tackle"],
            "Registeel": ["mortal-spin", "tackle", "tackle", "tackle"],
            "Arceus": ["springtide-storm", "tackle", "tackle", "tackle"],
            "Darkrai": ["lovely-kiss", "tackle", "tackle", "tackle"],
            "Diancie": ["moonlight", "tackle", "tackle", "tackle"],
            "Volcanion": ["thunderbolt", "tackle", "tackle", "tackle"],
            "Deoxys": ["fire-blast", "tackle", "tackle", "tackle"],
            "Latios": ["flash-cannon", "tackle", "tackle", "tackle"],
            "Mewtwo": ["extreme-speed", "tackle", "tackle", "tackle"],
            "Solgaleo": ["head-smash", "tackle", "tackle", "tackle"],
            "Lapras": ["shell-trap", "tackle", "tackle", "tackle"],
            "Politoed": ["recover", "tackle", "tackle", "tackle"],
            "Ampharos": ["tail-glow", "tackle", "tackle", "tackle"],
            "Xurkitree": ["soak", "tackle", "tackle", "tackle"],
            "Charizard": ["raging-fury", "tackle", "tackle", "tackle"],
            "Sharpedo": ["obstruct", "tackle", "tackle", "tackle"],
            "Trevenant": ["strength-sap", "tackle", "tackle", "tackle"],
            "Ninetales": ["yawn", "tackle", "tackle", "tackle"],
            "Raticate-alola": ["no-retreat", "tackle", "tackle", "tackle"],
            "Espeon": ["mystical-power", "tackle", "tackle", "tackle"],
            "Sigilyph": ["psycho-boost", "tackle", "tackle", "tackle"],
            "Uxie": ["recover", "tackle", "tackle", "tackle"],
            "Regidrago": ["flamethrower", "tackle", "tackle", "tackle"],
            "Scovillain": ["sleep-powder", "tackle", "tackle", "tackle"],
            "Tinkaton": ["tidy-up", "tackle", "tackle", "tackle"],
            "Jirachi": ["tri-attack", "tackle", "tackle", "tackle"],
            "Gardevoir": ["boomburst", "tackle", "tackle", "tackle"],
            "Rayquaza": ["collision-course", "tackle", "tackle", "tackle"],
            "Leafeon": ["jungle-healing", "tackle", "tackle", "tackle"],
            "Hydreigon": ["geomancy", "tackle", "tackle", "tackle"],
            "Azumarill": ["sucker-punch", "tackle", "tackle", "tackle"],
            "Groudon": ["hydro-stream", "tackle", "tackle", "tackle"],
            "Dhelmise": ["double-iron-bash", "tackle", "tackle", "tackle"],
            "Electivire": ["plasma-fists", "tackle", "tackle", "tackle"],
            "Magmortar": ["blue-flare", "tackle", "tackle", "tackle"],
            "Rhyperior": ["strength-sap", "tackle", "tackle", "tackle"],
            "Kyogre": ["hurricane", "tackle", "tackle", "tackle"],
            "Cobalion": ["clangorous-soul", "tackle", "tackle", "tackle"],
            "Camerupt": ["magma-storm", "tackle", "tackle", "tackle"],
            "Absol": ["victory-dance", "tackle", "tackle", "tackle"],
            "Spiritomb": ["toxic-thread", "tackle", "tackle", "tackle"],
            "Manectric": ["nasty-plot", "tackle", "tackle", "tackle"],
            "Greninja": ["strange-steam", "tackle", "tackle", "tackle"],
            "Rabsca": ["quiver-dance", "tackle", "tackle", "tackle"],
            "Lokix": ["fell-stinger", "tackle", "tackle", "tackle"],
            "Koraidon": ["dragon-dance", "tackle", "tackle", "tackle"],
            "Dialga": ["hydro-pump", "tackle", "tackle", "tackle"],
            "Necrozma": ["secret-sword", "tackle", "tackle", "tackle"],
            "Beedrill": ["megahorn", "tackle", "tackle", "tackle"],
            "Heracross": ["u-turn", "tackle", "tackle", "tackle"],
            "Manaphy": ["stored-power", "tackle", "tackle", "tackle"],
            "Pidgeot": ["focus-blast", "tackle", "tackle", "tackle"],
            # "Salamence": ["crush-grip", "tackle", "tackle", "tackle"],
            "Gallade": ["no-retreat", "tackle", "tackle", "tackle"],
            "Gogoat": ["body-press", "tackle", "tackle", "tackle"],
            "Pyroar": ["fiery-dance", "tackle", "tackle", "tackle"],
            "Aegislash": ["behemoth-blade", "tackle", "tackle", "tackle"],
            "Braviary-hisui": ["aeroblast", "tackle", "tackle", "tackle"],
            "Druddigon": ["diamond-storm", "tackle", "tackle", "tackle"],
            "Raikou": ["geomancy", "tackle", "tackle", "tackle"],
            "Zacian": ["flying-press", "tackle", "tackle", "tackle"],
            "Celebi": ["quiver-dance", "tackle", "tackle", "tackle"],
            "Lugia": ["oblivion-wing", "tackle", "tackle", "tackle"],
            "Bellossom": ["powder", "tackle", "tackle", "tackle"],
            "Vileplume": ["toxic-thread", "tackle", "tackle", "tackle"],
            "Corviknight": ["anchor-shot", "tackle", "tackle", "tackle"],
            "Slaking": ["skill-swap", "tackle", "tackle", "tackle"],
            "Ceruledge": ["leaf-blade", "tackle", "tackle", "tackle"],
            "Breloom": ["triple-axel", "tackle", "tackle", "tackle"],
            "Cloyster": ["water-shuriken", "tackle", "tackle", "tackle"],
            "Cinderace": ["trop-kick", "tackle", "tackle", "tackle"],
            "Poliwrath": ["jet-punch", "tackle", "tackle", "tackle"],
            "Meloetta": ["iron-head", "tackle", "tackle", "tackle"],
            "Bibarel": ["clangorous-soul", "tackle", "tackle", "tackle"],
            "Blaziken": ["fake-out", "tackle", "tackle", "tackle"],
            "Blastoise": ["origin-pulse", "tackle", "tackle", "tackle"],
            "Drapion": ["wicked-blow", "tackle", "tackle", "tackle"],
            #"Guzzlord": ["fillet away", "tackle", "tackle", "tackle"],

        }

    async def get_time(self):
        now = datetime.now()
        now = now.astimezone(ZoneInfo("EST"))
        now_time = now.time()
        display_time = now.strftime("%m/%d/%Y, %I:%M:%S %p")
        if now_time >= time(6, 00) and now_time <= time(17, 59):
            night = False
        else:
            night = True
        return night, display_time

    async def remove_poke(self, user_id: int, poke_id: int, delete: bool = False):
        """
        Helper func to remove a pokemon from a user's array.

        This func handles de-selecting the pokemon and removing it from the user's party.
        """
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT pokes, selected, party FROM users WHERE u_id = $1", user_id
            )
            if data is None:
                raise UserNotStartedError
            pokes, selected, party = data
            if poke_id not in pokes:
                return
            selected = None if selected == poke_id else selected
            party = [0 if p == poke_id else p for p in party]
            await pconn.execute(
                "UPDATE users SET pokes = array_remove(pokes, $2), selected = $3, party = $4 WHERE u_id = $1",
                user_id,
                poke_id,
                selected,
                party,
            )
            if delete:
                await pconn.execute("DELETE FROM pokes WHERE id = $1", poke_id)
            else:
                await pconn.execute(
                    "UPDATE pokes SET fav = false WHERE id = $1", poke_id
                )

    async def shadow_hunt_check(self, user_id: int, pokemon: str):
        """
        Rolls for a shadow pokemon.

        Returns True if the given user should get a shadow skin for the given pokemon, False otherwise.
        """
        make_shadow = False
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow(
                "SELECT hunt, chain FROM users WHERE u_id = $1", user_id
            )
            if data is None:
                return False
            hunt, chain = data
            if hunt != pokemon.capitalize():
                return False

            # get pat tier
            patreon = await self.bot.patreon_tier(user_id)

            make_shadow = random.random() < (
                (1 / 12000 - (12000 * 0.25 if patreon == "Rarity Hunter" else 0))
                * (4 ** (chain / 1000))
            )
            if make_shadow:
                await pconn.execute(
                    "UPDATE users SET chain = 0 WHERE u_id = $1", user_id
                )
            else:
                await pconn.execute(
                    "UPDATE users SET chain = chain + 1 WHERE u_id = $1", user_id
                )
        return make_shadow

    # Incase we ever add it
    # Would need separate 'hunt' and 'chain' columns within the user table
    async def shiny_hunt_check(self, user_id: int, pokemon: str):
        """
        Checks hunt status to determine
        Whether Pokemon should/should not be Shiny.

        This actually returns True or False for shiny determination
        """
        make_shiny = False
        threshold = 4096
        async with self.bot.db[0].acquire() as pconn:
            # Pull data for check
            data = await pconn.fetchrow(
                "SELECT hunt, chain FROM users WHERE u_id = $1", user_id
            )
            if data is None:
                return False
            hunt, chain = data
            # First to see if current chain results in shiny
            if hunt != pokemon.capitalize():  # Spawn does not match hunt
                make_shiny = random.choice([False for i in range(threshold)] + [True])
            else:
                make_shiny = random.choice(
                    [False for i in range(threshold - chain)] + [True]
                )
                # Either reset chain or increase depending on results
                if make_shiny:
                    await pconn.execute(
                        "UPDATE users SET chain = 0 WHERE u_id = $1", user_id
                    )
                else:
                    await pconn.execute(
                        "UPDATE users SET chain = chain + 1 WHERE u_id = $1", user_id
                    )
        return make_shiny

    async def create_poke(
        self,
        bot,
        user_id: int,
        pokemon: str,
        *,
        boosted: bool = False,
        radiant: bool = False,
        shiny: bool = False,
        skin: str = None,
        gender: str = None,
        level: int = 1,
        tradable: bool = True,
        name: str = "",
    ):
        """
        Creates a poke and gives it to user.

        Returns a Pokemon object if the poke was created, and None otherwise.
        """
        if name:
            form_info = await self.bot.db[1].forms.find_one({"identifier": name.lower()}) # If we passed an Egg, with its hatch/parent name, then check that instead.
        else:
            form_info = await self.bot.db[1].forms.find_one({"identifier": pokemon.lower()})
        try:
            pokemon_info = await self.bot.db[1].pfile.find_one(
                {"id": form_info["pokemon_id"]}
            )
            gender_rate = pokemon_info["gender_rate"]
        except Exception:
            self.bot.logger.warn("No Gender Rate for %s" % pokemon.lower())
            return None

        ab_ids = (
            await self.bot.db[1]
            .poke_abilities.find({"pokemon_id": form_info["pokemon_id"]})
            .to_list(length=3)
        )
        ab_ids = [doc["ability_id"] for doc in ab_ids]

        min_iv = 15 if boosted else 1
        max_iv = random.randint(29, 31) if boosted else 29
        hpiv = random.randint(min_iv, max_iv)
        atkiv = random.randint(min_iv, max_iv)
        defiv = random.randint(min_iv, max_iv)
        spaiv = random.randint(min_iv, max_iv)
        spdiv = random.randint(min_iv, max_iv)
        speiv = random.randint(min_iv, max_iv)
        nature = random.choice(natlist)
        if not gender:
            # Gender
            if "idoran-" in pokemon:
                gender = pokemon[-2:]
            elif pokemon.lower() == "illumise":
                gender = "-f"
            elif pokemon.lower() in ("volbeat", "tauros-paldea"):
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

        if skin:
            shiny = False
            radiant = False
            skin = skin.lower()
        elif radiant:
            shiny = False
        elif not shiny:
            override_with_shadow = await self.shadow_hunt_check(user_id, pokemon)
            if override_with_shadow:
                skin = "shadow"
                await bot.get_partial_messageable(998341289164689459).send(
                    f"`{user_id} - {pokemon}`"
                )
        emoji = get_emoji(
            shiny=shiny,
            radiant=radiant,
            skin=skin,
        )
        query2 = """
                INSERT INTO pokes (pokname, hpiv, atkiv, defiv, spatkiv, spdefiv, speediv, hpev, atkev, defev, spatkev, spdefev, speedev, pokelevel, moves, hitem, exp, nature, expcap, poknick, shiny, price, market_enlist, fav, ability_index, gender, caught_by, radiant, skin, tradable, name, counter)

                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32) RETURNING id
                """
        args = (
            pokemon.capitalize(),
            hpiv,
            atkiv,
            defiv,
            spaiv,
            spdiv,
            speiv,
            0,
            0,
            0,
            0,
            0,
            0,
            level,
            (
                ["tackle", "tackle", "tackle", "tackle"]
                if not skin == "alpha"
                else self.ALPHA_MOVESETS.get(pokemon.capitalize())
            ),
            "None",
            1,
            nature,
            level**2,
            "None",
            shiny,
            0,
            False,
            False,
            random.randrange(len(ab_ids)),
            gender,
            user_id,
            radiant,
            skin,
            tradable,
            name,
            256 if pokemon.capitalize() == "Egg" else 0,
        )
        async with self.bot.db[0].acquire() as pconn:
            pokeid = await pconn.fetchval(query2, *args)
            await pconn.execute(
                "UPDATE users SET pokes = array_append(pokes, $2) WHERE u_id = $1",
                user_id,
                pokeid,
            )
        return Pokemon(
            pokeid, gender, sum((hpiv, atkiv, defiv, spaiv, spdiv, speiv)), emoji
        )
        
    async def transfer_redeems(self, sender, receiver, amount, market: str = ""):
        market = market == "market"
        async with self.bot.db[0].acquire() as pconn:
            if market:
                await pconn.execute("UPDATE users SET redeems = redeems + $1 WHERE u_id = $2", amount, receiver.id)
                return
            await pconn.execute(
                "UPDATE users SET redeems = redeems - $1 WHERE u_id = $2",
                amount,
                sender.id,
            )
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                amount,
                receiver.id,
            )
            return True
    
    async def transfer_gems(self, sender, receiver, amount):
        async with self.bot.db[0].acquire() as pconn:
            await self.remove_bag_item(
                        sender.id,
                        "radiant_gem",
                        amount,
                        True,
                    )
            await self.add_bag_item(
                        receiver.id,
                        "radiant_gem",
                        amount,
                        True,
                    )
            return True
    
    async def transfer_credits(self, sender, receiver, amount):
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2",
                amount,
                sender.id,
            )
            await pconn.execute(
                "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                amount,
                receiver.id,
            )
            return True
            
    async def add_bag_item(
        self,
        user: int,
        item_name: str,
        quantity: int,
        bound=False,
    ):
        """
        Creates new bag for user and inserts item
        If user already has bag just insert item
        """
        async with self.bot.db[0].acquire() as pconn:
            # This can be removed after sometime
            # Create user's bag if doesn't exist
            await pconn.execute(
                "INSERT INTO bag (u_id) VALUES ($1) ON CONFLICT DO NOTHING", user
            )

            # Create user's account bound table if doesn't exist
            await pconn.execute(
                "INSERT INTO account_bound VALUES ($1) ON CONFLICT DO NOTHING", user
            )

            if bound:
                # Pull item's query from account bound dict above and execute query
                try:
                    query = ADD_BOUND_ITEM.get(item_name)
                except:
                    # Must have been bound
                    query = ADD_BAG_ITEM.get(item_name)
            else:
                # Pull item's query from bag dict above and execute query
                try:
                    query = ADD_BAG_ITEM.get(item_name)
                except:
                    query = ADD_BOUND_ITEM.get(item_name)

            args = (quantity, user)
            await pconn.execute(query, *args)
            return Item(item_name, quantity)

    async def remove_bag_item(
        self,
        user: int,
        item_name: str,
        quantity: int,
        bound=False,
    ):
        quantity = max(1, quantity)
        """
        Creates new bag for user and inserts item
        If user already has bag just insert item
        """
        async with self.bot.db[0].acquire() as pconn:
            if bound:
                # Pull item's query from account bound dict above and execute query
                query = REMOVE_BOUND_ITEM.get(item_name)
            else:
                # Pull item's query from bag dict above and execute query
                query = REMOVE_BAG_ITEM.get(item_name)

            args = (quantity, user)
            await pconn.execute(query, *args)
            return Item(item_name, quantity)

    class TradeLock:
        """
        A context manager for tradelocking users.

        Usage:
        async with TradeLock(ctx.bot, ctx.author, user):
            Code that requires tradelocking

        Any number of users can be passed after the bot param,
        and they will all be tradelocked for the entire duration of the context manager.
        """

        def __init__(self, bot, *users: discord.User):
            self.bot = bot
            self.users = users

        async def __aenter__(self):
            for user in self.users:
                await self.bot.redis_manager.redis.execute_command(
                    "LPUSH", "tradelock", str(user.id)
                )

        async def __aexit__(self, exc_type, exc_value, traceback):
            for user in self.users:
                await self.bot.redis_manager.redis.execute_command(
                    "LREM", "tradelock", "1", str(user.id)
                )
