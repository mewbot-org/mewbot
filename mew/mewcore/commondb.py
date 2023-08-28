import random
import discord

from mewcogs.pokemon_list import natlist
from mewutils.misc import get_emoji
from mewcore.items import *


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


class Item():
    """Dataclass to hold info about an added item"""
    def __init__(self, item_name, quantity):
        self.item_name = item_name
        self.quantity = quantity


class CommonDB:
    def __init__(self, bot):
        self.bot = bot
        self.ALPHA_MOVESETS = {
            'Golurk' : ['mach-punch', 'tackle', 'tackle', 'tackle'],
            'Snorlax': ['slack-off', 'tackle', 'tackle', 'tackle'],
            'Banette': ['topsy-turvy', 'tackle', 'tackle', 'tackle'],
            'Aerodactyl': ['brave-bird', 'tackle', 'tackle', 'tackle'],
            'Torterra': ['shell-smash', 'tackle', 'tackle', 'tackle'],
            'Goodra': ['core-enforcer', 'tackle', 'tackle', 'tackle'],
            }

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
                await pconn.execute(
                    "DELETE FROM pokes WHERE id = $1", 
                    poke_id
                )
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
            make_shadow = random.random() < ((1 / 12000) * (4 ** (chain / 1000)))
            if make_shadow:
                await pconn.execute(
                    "UPDATE users SET chain = 0 WHERE u_id = $1", user_id
                )
            else:
                await pconn.execute(
                    "UPDATE users SET chain = chain + 1 WHERE u_id = $1", user_id
                )
        return make_shadow

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
        tradable: bool = True
    ):
        """
        Creates a poke and gives it to user.

        Returns a Pokemon object if the poke was created, and None otherwise.
        """
        form_info = await bot.db[1].forms.find_one({"identifier": pokemon.lower()})
        try:
            pokemon_info = await bot.db[1].pfile.find_one(
                {"id": form_info["pokemon_id"]}
            )
            gender_rate = pokemon_info["gender_rate"]
        except Exception:
            bot.logger.warn("No Gender Rate for %s" % pokemon.lower())
            return None

        ab_ids = (
            await bot.db[1]
            .poke_abilities.find({"pokemon_id": form_info["pokemon_id"]})
            .to_list(length=3)
        )
        ab_ids = [doc["ability_id"] for doc in ab_ids]

        min_iv = 12 if boosted else 1
        max_iv = 31 if boosted or random.randint(0, 1) else 29
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
                INSERT INTO pokes (pokname, hpiv, atkiv, defiv, spatkiv, spdefiv, speediv, hpev, atkev, defev, spatkev, spdefev, speedev, pokelevel, moves, hitem, exp, nature, expcap, poknick, shiny, price, market_enlist, fav, ability_index, gender, caught_by, radiant, skin, tradable)

                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30) RETURNING id
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
            ["tackle", "tackle", "tackle", "tackle"] if not skin == 'alpha' else self.ALPHA_MOVESETS.get(pokemon.capitalize()),
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
        )
        async with bot.db[0].acquire() as pconn:
            pokeid = await pconn.fetchval(query2, *args)
            await pconn.execute(
                "UPDATE users SET pokes = array_append(pokes, $2) WHERE u_id = $1",
                user_id,
                pokeid,
            )
        return Pokemon(
            pokeid, gender, sum((hpiv, atkiv, defiv, spaiv, spdiv, speiv)), emoji
        )


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
            #This can be removed after sometime
            #Create user's bag if doesn't exist
            await pconn.execute(
                "INSERT INTO bag (u_id) VALUES ($1) ON CONFLICT DO NOTHING", 
                user
            )
            
            #Create user's account bound table if doesn't exist
            await pconn.execute(
                "INSERT INTO account_bound VALUES ($1) ON CONFLICT DO NOTHING",
                user
            )

            if bound:
                #Pull item's query from account bound dict above and execute query
                try:
                    query = ADD_BOUND_ITEM.get(item_name)
                except:
                    #Must have been bound
                    query = ADD_BAG_ITEM.get(item_name)
            else:
                #Pull item's query from bag dict above and execute query
                try:
                    query = ADD_BAG_ITEM.get(item_name)
                except:
                    query = ADD_BOUND_ITEM.get(item_name)

            args = (
                quantity,
                user
            )
            await pconn.execute(query, *args)
            return Item(item_name, quantity)
    
    
    async def remove_bag_item(
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
            if bound:
                #Pull item's query from account bound dict above and execute query
                query = REMOVE_BOUND_ITEM.get(item_name)
            else:
                #Pull item's query from bag dict above and execute query
                query = REMOVE_BAG_ITEM.get(item_name)

            args = (
                quantity,
                user
            )
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
                await self.bot.redis_manager.redis.execute(
                    "LPUSH", "tradelock", str(user.id)
                )

        async def __aexit__(self, exc_type, exc_value, traceback):
            for user in self.users:
                await self.bot.redis_manager.redis.execute(
                    "LREM", "tradelock", "1", str(user.id)
                )
