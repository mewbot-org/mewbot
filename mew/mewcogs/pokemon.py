import math
import discord
from discord.ext import commands

import random
import asyncpg
import subprocess
import asyncio
import sys
from io import BytesIO
from datetime import datetime, timedelta
from typing import Literal
import time


from mewcogs.json_files import *
from mewcogs.pokemon_list import *
from mewutils.misc import (
    get_pokemon_image,
    get_emoji,
    pagify,
    MenuView,
    ConfirmView,
    AsyncIter,
)
from mewutils.checks import tradelock
from pokemon_utils.utils import get_pokemon_info, get_pokemon_qinfo


custom_poke = (
    "Onehitmonchan",
    "Xerneas-brad",
    "Lucariosouta",
    "Cubone-freki",
    "Glaceon-glaceon",
    "Scorbunny-sav",
    "Palkia-gompp",
    "Alacatzam",
    "Magearna-curtis",
    "Arceus-tatogod",
    "Enamorus-therian-forme",
    "Kubfu-rapid-strike",
    "Palkia-lord",
    "Dialga-lord",
    "Missingno",
)


class Pokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.forms_cursor = bot.db[1].forms.find()

    async def parse_form(self, form):
        form = form.lower()
        if (
            "-" not in form
            or form.startswith("tapu-")
            or form.startswith("ho-")
            or form.startswith("mr-")
            or form.startswith("nidoran-")
        ):
            return form
        if form in (await self.forms_cursor.distinct("identifier")):
            return form
        if is_formed(form) and form.split("-")[1] in (
            await self.forms_cursor.distinct("form_identifier")
        ):
            return form
        # possible 'mega charizard' 'mega charizard x' expecting 'charizard mega x' or 'charizard mega'
        form = list(form.split("-"))
        form[0], form[1] = form[1], form[0]
        form = "-".join(form)
        return form
    
    @commands.hybrid_group()
    async def pokedex(self, ctx):
        """Pokedex Commands"""
        pass
    
    @pokedex.command()
    async def national(self, ctx, shiny:Literal['True', 'False']):
        """View Caught & Uncaught Pokémon."""
        await self._build_pokedex(ctx, True, shiny)

    @pokedex.command()
    async def unowned(self, ctx, shiny:Literal['True', 'False']):
        """View Uncaught Pokémon."""
        await self._build_pokedex(ctx, False, shiny)

    async def _build_pokedex(self, ctx, include_owned: bool, shiny:bool):
        """Helper func to build & send the pokedex."""
        async with self.bot.db[0].acquire() as pconn:
            msg = ''
            pokes = await pconn.fetchval(
                "SELECT pokes FROM users WHERE u_id = $1", ctx.author.id
            )
            if pokes is None:
                return
            if shiny == 'True':
                msg = 'Shiny '
                owned = await pconn.fetch(
                    "SELECT DISTINCT pokname FROM pokes WHERE id = ANY($1) AND pokname != ANY($2) AND shiny = True",
                    pokes,
                    custom_poke,
                )
            else:
                owned = await pconn.fetch(
                    "SELECT DISTINCT pokname FROM pokes WHERE id = ANY($1) AND pokname != ANY($2)",
                    pokes,
                    custom_poke,
                )
        allpokes = self.bot.db[1].pfile.find(
            projection={"identifier": True, "_id": False}
        )
        allpokes = await allpokes.to_list(None)
        allpokes = [t["identifier"].capitalize() async for t in AsyncIter(allpokes)]
        total = set(allpokes) - set(custom_poke)
        owned = set([t["pokname"] async for t in AsyncIter(owned)])
        owned &= total
        desc = ""
        async for poke in AsyncIter(allpokes):
            if poke not in total:
                continue
            if poke not in owned:
                desc += f"**{poke}** - <a:abrillianceCROSSX:1044340450938589204>\n"
            elif include_owned:
                desc += f"**{poke}** - <a:check_arn:1044340391748571136>\n"
        embed = discord.Embed(
            title=f"{msg}Pokedex for {ctx.author.name}\nYou have {len(owned)} out of {len(total)}!",
            colour=random.choice(self.bot.colors),
        )
        pages = pagify(desc, per_page=20, base_embed=embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_command()
    @discord.app_commands.describe(
        pokemon="Can be <pokemon_number> or 'new', 'latest' for most recent Pokémon or blank for currently selected Pokémon."
    )
    async def select(self, ctx, pokemon: str):
        """Select a Pokémon"""
        async with self.bot.db[0].acquire() as pconn:
            if pokemon in ("newest", "new", "latest"):
                _id = await pconn.fetchval(
                    "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1",
                    ctx.author.id,
                )
            else:
                try:
                    pokemon = int(pokemon)
                except ValueError:
                    await ctx.send("`/select <pokemon_number>` to select a Pokemon!")
                    return
                if pokemon > 2147483647:
                    await ctx.send("You do not have that many pokemon!")
                    return
                _id = await pconn.fetchval(
                    "SELECT pokes[$1] FROM users WHERE u_id = $2",
                    pokemon,
                    ctx.author.id,
                )
            if _id is None:
                await ctx.send("You have not started or that Pokemon does not exist!")
                return
            else:
                name = await pconn.fetchval(
                    "SELECT pokname FROM pokes WHERE id = $1", _id
                )
                await pconn.execute(
                    "UPDATE users SET selected = $1 WHERE u_id = $2", _id, ctx.author.id
                )
            emoji = random.choice(emotes)
            await ctx.send(f"You have selected your {name}\n{emoji}")

    @commands.hybrid_command()
    @discord.app_commands.describe(
        pokemon="Can be <pokemon_number> or 'new', 'latest' for your most recently owned Pokémon."
    )
    @tradelock
    async def release(self, ctx, pokemon):
        """Release a Pokémon"""
        pokes = []
        if pokemon.lower() in ("new", "latest"):
            async with self.bot.db[0].acquire() as pconn:
                poke = await pconn.fetchval(
                    "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1 AND array_length(pokes, 1) > 1",
                    ctx.author.id,
                )
                if poke is None:
                    await ctx.send("You don't have any pokemon you can release!")
                    return
                pokes.append(poke)
        else:
            async with self.bot.db[0].acquire() as pconn:
                stmt = await pconn.prepare(
                    "SELECT pokes[$1] FROM users WHERE u_id = $2"
                )
                for p in pokemon.split():
                    try:
                        p = int(p)
                        if p <= 1:
                            continue
                        id = await stmt.fetchval(p, ctx.author.id)
                        if not id:
                            continue
                        pokes.append(id)
                    except ValueError:
                        continue
            if not pokes:
                await ctx.send("You did not specify any valid pokemon!")
                return
        async with self.bot.db[0].acquire() as pconn:
            pokenames = []
            favorites = []
            valid_pokes = []
            for p in await pconn.fetch(
                "SELECT id, pokname, fav, COALESCE(atkiv,0) + COALESCE(defiv,0) + COALESCE(spatkiv,0) + COALESCE(spdefiv,0) + COALESCE(speediv,0) + COALESCE(hpiv,0) AS ivs FROM pokes WHERE id = ANY ($1)",
                pokes,
            ):
                if p["fav"]:
                    favorites.append(p["pokname"])
                else:
                    pokenames.append(f'{p["pokname"]} ({p["ivs"]/186:06.2%})')
                    valid_pokes.append(p["id"])
        if favorites:
            await ctx.send(
                f"You cannot release your {', '.join(favorites).capitalize()} as they are favorited.\n"
                f"Unfavorite them first with `/fav remove <poke>`."
            )
        if not pokenames:
            return
        if not await ConfirmView(
            ctx,
            f"Are you sure you want to release your {', '.join(pokenames).capitalize()}?",
        ).wait():
            await ctx.send("Release cancelled.")
            return
        for poke_id in valid_pokes:
            await self.bot.commondb.remove_poke(ctx.author.id, poke_id, delete=False)
        await ctx.send(
            f"You have successfully released your {', '.join(pokenames).capitalize()}"
        )
        await self.bot.get_partial_messageable(998563289082626049).send(
            f"{ctx.author} (`{ctx.author.id}`) released **{len(valid_pokes)}** pokes.\n`{valid_pokes}`"
        )

    # @commands.hybrid_command()
    async def cooldowns(self, ctx):
        await ctx.send(
            "This command is deprecated, you should use `/f p args:cooldown` instead. "
            "It has the same functionality, but with a fresh output and the ability to use additional filters.\n"
            "Running that for you now..."
        )
        await asyncio.sleep(3)
        c = ctx.bot.get_cog("Filter")
        if c is None:
            return
        await c.filter_pokemon.callback(c, ctx, args="cooldown")
        return

    @commands.hybrid_command()
    async def p(self, ctx):
        """List all your currently owned Pokémon"""
        async with ctx.bot.db[0].acquire() as pconn:
            pokes = await pconn.fetchval(
                "SELECT pokes FROM users WHERE u_id = $1", ctx.author.id
            )
            if pokes is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            user_order = await pconn.fetchval(
                "SELECT user_order FROM users WHERE u_id = $1", ctx.author.id
            )

        orders = {
            "iv": "ORDER by ivs DESC",
            "level": "ORDER by pokelevel DESC",
            "ev": "ORDER by evs DESC",
            "name": "order by pokname DESC",
            "kek": "",
        }
        order = orders.get(user_order)
        query = f"""SELECT *, COALESCE(atkiv,0) + COALESCE(defiv,0) + COALESCE(spatkiv,0) + COALESCE(spdefiv,0) + COALESCE(speediv,0) + COALESCE(hpiv,0) AS ivs, COALESCE(atkev,0) + COALESCE(defev,0) + COALESCE(spatkev,0) + COALESCE(spdefev,0) + COALESCE(speedev,0) + COALESCE(hpev,0) AS evs FROM pokes WHERE id = ANY ($1) {order}"""

        async with self.bot.db[0].acquire() as pconn:
            async with pconn.transaction():
                cur = await pconn.cursor(query, pokes)
                records = await cur.fetch(15 * 250)

        desc = ""
        async for record in AsyncIter(records):
            nr = record["pokname"]
            pn = pokes.index(record["id"]) + 1
            nick = record["poknick"]
            iv = record["ivs"]
            shiny = record["shiny"]
            radiant = record["radiant"]
            level = record["pokelevel"]
            emoji = get_emoji(
                blank="<:blank:1012504803496177685>",
                shiny=shiny,
                radiant=radiant,
                skin=record["skin"],
            )
            gender = ctx.bot.misc.get_gender_emote(record["gender"])
            desc += f"{emoji}{gender}**{nr.capitalize()}** | **__No.__** - {pn} | **Level** {level} | **IV%** {iv/186:.2%}\n"

        embed = discord.Embed(title="Your Pokémon", color=0xFFB6C1)
        pages = pagify(desc, base_embed=embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_group()
    async def tags(self, ctx):
        ...

    @tags.command()
    @discord.app_commands.describe(
        numbers="Set to True if you would like tags shown by Pokemon ID",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def all(self, ctx, numbers: Literal["True", "False"]):
        """See a complete list of tags assigned to your Pokemon"""
        async with ctx.bot.db[0].acquire() as pconn:
            poke_ids = await pconn.fetchval(
                "SELECT pokes FROM users WHERE u_id = $1", ctx.author.id
            )
            tag_data = await pconn.fetch(
                "SELECT id, tags FROM pokes WHERE id = ANY($1) ORDER BY id ASC",
                poke_ids,
            )
        ids = [record["id"] for record in tag_data]
        tag_data = [record["tags"] for record in tag_data]
        embed = discord.Embed(
            title="Your Pokemon Tags",
            description="Hope there's nothing bad!!",
            color=0x000084,
        )
        desc = ""
        tag_array = []

        if numbers == "True":
            for idx, id in enumerate(ids):
                tag = tag_data[idx]
                if len(tag) != 0:
                    pn = poke_ids.index(id) + 1
                    tag = ",".join(tag)
                    desc += f"`ID`: {pn} - `Tags`: {tag}\n"
        else:
            for idx, id in enumerate(ids):
                tags = tag_data[idx]
                if len(tags) != 0:
                    for tag in tags:
                        if tag not in tag_array:
                            tag_array.append(tag)
                            desc += f"{tag}\n"

        pages = pagify(desc, base_embed=embed)
        await MenuView(ctx, pages).start()

    @tags.command()
    @discord.app_commands.describe(
        pokemon="Can be <pokemon_number> or 'new', 'latest' for most recently owned Pokémon."
    )
    async def list(self, ctx, pokemon: str):
        """View the tags for a pokemon."""
        async with self.bot.db[0].acquire() as pconn:
            if pokemon.lower() in ("new", "latest"):
                gid = await pconn.fetchval(
                    "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1 AND array_length(pokes, 1) > 1",
                    ctx.author.id,
                )
            else:
                try:
                    pokemon = int(pokemon)
                except ValueError:
                    await ctx.send("You need to provide a valid pokemon number.")
                    return
                gid = await pconn.fetchval(
                    "SELECT pokes[$1] FROM users WHERE u_id = $2",
                    pokemon,
                    ctx.author.id,
                )
            if gid is None:
                await ctx.send("That pokemon does not exist!")
                return
            tags = await pconn.fetchval("SELECT tags FROM pokes WHERE id = $1", gid)
        if not tags:
            await ctx.send(
                f"That Pokémon has no tags! Use `/tags add <tag> {pokemon}` to add one!"
            )
            return
        tags = ", ".join(tags)
        tags = f"**Current tags:** {tags}"
        pages = pagify(tags, sep=", ", per_page=30)
        await MenuView(ctx, pages).start()

    @tags.command()
    @discord.app_commands.describe(
        tag="A 'Tag' or 'Label' to give a Pokémon or list of Pokémon",
        pokes="List of Pokémon to tag.",
    )
    async def add(self, ctx, tag: str, pokes: str):
        """Add a tag to a pokemon."""
        tag = tag.lower().strip()
        pokes = pokes.split(" ")
        if " " in tag:
            await ctx.send("Tags cannot have spaces!")
            return
        if len(tag) > 50:
            await ctx.send("That tag is too long!")
            return
        failed = []
        async with ctx.bot.db[0].acquire() as pconn:
            for poke in pokes:
                if poke.lower() in ("new", "latest"):
                    gid = await pconn.fetchval(
                        "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1 AND array_length(pokes, 1) > 1",
                        ctx.author.id,
                    )
                else:
                    try:
                        poke = int(poke)
                    except ValueError:
                        failed.append(str(poke))
                        continue
                    gid = await pconn.fetchval(
                        "SELECT pokes[$1] FROM users WHERE u_id = $2",
                        poke,
                        ctx.author.id,
                    )
                if gid is None:
                    failed.append(str(poke))
                    continue
                tags = await pconn.fetchval("SELECT tags FROM pokes WHERE id = $1", gid)
                try:
                    tags = set(tags)
                except TypeError:
                    failed.append(str(poke))
                    continue
                tags.add(tag)
                await pconn.execute(
                    "UPDATE pokes SET tags = $1 WHERE id = $2", list(tags), gid
                )
        if len(failed) == len(pokes) == 1:
            await ctx.send("That pokemon does not exist!")
        elif len(failed) == len(pokes):
            await ctx.send("Those pokemon do not exist!")
        elif failed:
            await ctx.send(
                f"Tag successfully added to existing pokemon. The following pokemon I could not find: {', '.join(failed)}"
            )
        else:
            await ctx.send("Tag successfully added.")

    @tags.command()
    @discord.app_commands.describe(
        tag="A 'Tag' or 'Label' on a Pokémon or list of Pokémon",
        pokes="List of Pokémon to remove the tag.",
    )
    async def remove(self, ctx, tag: str, pokes: str):
        """Remove a tag from a pokemon."""
        tag = tag.lower().strip()
        pokes = pokes.split(" ")
        if " " in tag:
            await ctx.send("Tags cannot have spaces!")
            return
        not_exist = []
        dont_have_tag = []

        async with ctx.bot.db[0].acquire() as pconn:
            for poke in pokes:
                if poke.lower() in ("new", "latest"):
                    gid = await pconn.fetchval(
                        "SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1 AND array_length(pokes, 1) > 1",
                        ctx.author.id,
                    )
                else:
                    try:
                        poke = int(poke)
                    except ValueError:
                        not_exist.append(str(poke))
                        continue
                    gid = await pconn.fetchval(
                        "SELECT pokes[$1] FROM users WHERE u_id = $2",
                        poke,
                        ctx.author.id,
                    )
                if gid is None:
                    not_exist.append(str(poke))
                    continue
                tags = await pconn.fetchval("SELECT tags FROM pokes WHERE id = $1", gid)
                try:
                    tags = set(tags)
                except TypeError:
                    not_exist.append(str(poke))
                    continue
                if tag not in tags:
                    dont_have_tag.append(str(poke))
                    continue
                tags.remove(tag)
                await pconn.execute(
                    "UPDATE pokes SET tags = $1 WHERE id = $2", list(tags), gid
                )
        # I don't know why I did this
        if (len(not_exist) + len(dont_have_tag) == len(pokes)) and (
            not_exist and dont_have_tag
        ):
            await ctx.send(
                f"Failed to remove tags from specified pokemon. The following pokemon could not be found: {', '.join(not_exist)}. "
                f"The following pokemon did not have that tag: {', '.join(dont_have_tag)}."
            )
        elif len(not_exist) == len(pokes) == 1:
            await ctx.send("That pokemon does not exist!")
        elif len(not_exist) == len(pokes):
            await ctx.send("Those pokemon do not exist!")
        elif len(dont_have_tag) == len(pokes) == 1:
            await ctx.send("That pokemon does not have that tag!")
        elif len(dont_have_tag) == len(pokes):
            await ctx.send("Those pokemon do not have that tag!")
        elif not_exist and dont_have_tag:
            await ctx.send(
                f"Tag successfully removed from existing pokemon that had the tag.  The following pokemon could not be found: {', '.join(not_exist)}. "
                f"The following pokemon did not have that tag: {', '.join(dont_have_tag)}."
            )
        elif not_exist:
            await ctx.send(
                f"Tag successfully removed from existing pokemon. The following pokemon could not be found: {', '.join(not_exist)}."
            )
        elif dont_have_tag:
            await ctx.send(
                f"Tag successfully removed from pokemon with that tag.  The following pokemon did not have that tag: {', '.join(dont_have_tag)}."
            )
        else:
            await ctx.send("Tag successfully removed.")

    async def get_reqs(self, poke):
        """Gets a string formatted to be used to display evolution requirements for a particular pokemon."""
        reqs = []
        evoreq = await self.bot.db[1].evofile.find_one({"evolved_species_id": poke})
        if evoreq["trigger_item_id"]:
            item = await self.bot.db[1].items.find_one(
                {"id": evoreq["trigger_item_id"]}
            )
            reqs.append(f"apply `{item['identifier']}`")
        if evoreq["held_item_id"]:
            item = await self.bot.db[1].items.find_one({"id": evoreq["held_item_id"]})
            reqs.append(f"hold `{item['identifier']}`")
        if evoreq["gender_id"]:
            reqs.append(f"is `{'female' if evoreq['gender_id'] == 1 else 'male'}`")
        if evoreq["minimum_level"]:
            reqs.append(f"lvl `{evoreq['minimum_level']}`")
        if evoreq["known_move_id"]:
            move = await self.bot.db[1].moves.find_one({"id": evoreq["known_move_id"]})
            reqs.append(f"knows `{move['identifier']}`")
        if evoreq["minimum_happiness"]:
            reqs.append(f"happiness `{evoreq['minimum_happiness']}`")
        if evoreq["relative_physical_stats"] is not None:
            if evoreq["relative_physical_stats"] == 0:
                reqs.append(f"atk = def")
            elif evoreq["relative_physical_stats"] == 1:
                reqs.append(f"atk > def")
            elif evoreq["relative_physical_stats"] == -1:
                reqs.append(f"atk < def")
        if evoreq["region"]:
            reqs.append(f"region `{evoreq['region']}`")
        reqs = ", ".join(reqs)
        return f"({reqs})"

    async def get_kids(self, raw, species_id, prefix):
        """Recursively build an evolution tree for a particular species."""
        result = ""
        for poke in raw:
            if poke["evolves_from_species_id"] == species_id:
                reqs = ""
                if species_id:
                    reqs = await self.get_reqs(poke["id"])
                result += f"{prefix}├─{poke['identifier'].capitalize()} {reqs}\n"
                result += await self.get_kids(raw, poke["id"], f"{prefix}│")
        return result

    # async def get_kids(self, raw, species_id, prefix):
    #     """Recursively build an evolution tree for a particular species."""
    #     result = ""
    #     for index, poke in enumerate(raw):
    #         if poke['evolves_from_species_id'] == species_id or isinstance(poke['evolves_from_species_id'], float):
    #             self.bot.logger.info(
    #                 "Getting kids for %s " % poke['identifier']
    #             )
    #             # if math.isnan(poke["evolves_from_species_id"]):
    #             #     break
    #             #     if isinstance(poke["evolves_from_species_id"], float):
    #             #         self.bot.logger.warn(
    #             #             "Found a base evo %s " % poke['identifier']
    #             #         )
    #             #         continue

    #             reqs = ""
    #             if isinstance(poke["evolves_from_species_id"], int):
    #                 reqs = await self.get_reqs(poke["id"])
    #             result += f"{prefix}├─{poke['identifier']} {reqs}\n"
    #             result += await self.get_kids(raw, poke["id"], f"{prefix}│ ")
    #     return result

    @commands.hybrid_command(name="i")
    @discord.app_commands.describe(
        pokemon="Can be <pokemon_number> | <pokemon_name> or 'new', 'latest' for most recent Pokémon or blank for currently selected Pokémon."
    )
    async def info(self, ctx, *, pokemon: str = None, type: Literal['Shiny', 'Gleam', 'Radiant', 'Alpha', 'Shadow'] = "None"):
        """Get information about a Pokémon."""
        if pokemon is None:
            async with ctx.bot.db[0].acquire() as pconn:
                records = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                    ctx.author.id,
                )
            if records is None:
                await ctx.send(
                    f"You do not have a pokemon selected. Use `/select` to select one!"
                )
                return
            await ctx.send(embed=await get_pokemon_info(ctx, records))
            return

        if pokemon in ("newest", "latest", "atest", "ewest", "new"):
            async with ctx.bot.db[0].acquire() as pconn:
                records = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1)",
                    ctx.author.id,
                )
            if records is None:
                await ctx.send("You have not started!\nStart with `/start` first.")
                return
            await ctx.send(embed=await get_pokemon_info(ctx, records))
            return

        try:
            pokemon = int(pokemon)
        except ValueError:
            pass
        else:
            if pokemon < 1:
                await ctx.send("That is not a valid pokemon number!")
                return
            if pokemon > 4000000000:
                await ctx.send("You probably don't have that many pokemon...")
                return
            async with ctx.bot.db[0].acquire() as pconn:
                records = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT pokes[$1] FROM users WHERE u_id = $2)",
                    pokemon,
                    ctx.author.id,
                )
            if records is None:
                await ctx.send(
                    "You do not have that many pokemon. Go catch some more first!"
                )
                return
            await ctx.send(embed=await get_pokemon_info(ctx, records))
            return

        # "pokemon" is *probably* a pokemon name
        pokemon = pokemon.lower().replace("alolan", "alola").split()
        shiny = False
        skin = None
        if "Shiny" in type:
            shiny = True
            #pokemon.remove("shiny")
        elif "Gleam" in type:
            skin = "gleam"
            #pokemon.remove("gleam")
        elif "Alpha" in type:
            skin = "alpha"
            #pokemon.remove("alpha")
        elif "Radiant" in type:
            skin = "radiant"
            #pokemon.remove("radiant")
        elif "Shadow" in type:
            skin = "shadow"
            #pokemon.remove("shadow")
        pokemon = "-".join(pokemon)
        val = pokemon.capitalize()

        try:
            val = await self.parse_form(val)
            iurl = await get_pokemon_image(val, ctx.bot, shiny, skin=skin)
        except ValueError:
            await ctx.send("That Pokemon does not exist!")
            return

        forms = []
        if val.lower() in ("spewpa", "scatterbug", "mew"):
            forms = ["None"]
        else:
            # TODO: This is potentially VERY dangerous since this is user input directed to a regex pattern.
            cursor = ctx.bot.db[1].forms.find({"identifier": {"$regex": f".*{val}.*"}})
            forms = [t.capitalize() for t in await cursor.distinct("form_identifier")]

        if "" in forms:
            forms.remove("")
        if "Galar" in forms:
            forms.remove("Galar")
        if "Alola" in forms:
            forms.remove("Alola")
        if "Hisui" in forms:
            forms.remove("Hisui")
        if "Paldea" in forms:
            forms.remove("Paldea")
        if not forms:
            forms = ["None"]
        forms = "\n".join(forms)

        form_info = await ctx.bot.db[1].forms.find_one({"identifier": val.lower()})
        if not form_info:
            await ctx.send("That Pokemon does not exist!")
            return
        ptypes = await ctx.bot.db[1].ptypes.find_one({"id": form_info["pokemon_id"]})
        if not ptypes:
            await ctx.send("That Pokemon does not exist!")
            return
        type_ids = ptypes["types"]
        types = [
            str(
                ctx.bot.misc.get_type_emote(
                    (await ctx.bot.db[1].types.find_one({"id": _type}))["identifier"]
                )
            )
            for _type in type_ids
        ]
        try:
            egg_groups_ids = (
                await ctx.bot.db[1].egg_groups.find_one(
                    {"species_id": form_info["pokemon_id"]}
                )
            )["egg_groups"]
        except:
            egg_groups_ids = [15]

        egg_groups = [
            str(
                ctx.bot.misc.get_egg_emote(
                    (
                        await ctx.bot.db[1].egg_groups_info.find_one(
                            {"id": egg_group_id}
                        )
                    )["identifier"]
                )
            )
            for egg_group_id in egg_groups_ids
        ]

        ab_ids = []
        async for record in ctx.bot.db[1].poke_abilities.find(
            {"pokemon_id": form_info["pokemon_id"]}
        ):
            ab_ids.append(record["ability_id"])
        ab_id = ab_ids[0]
        abilities = [
            (await ctx.bot.db[1].abilities.find_one({"id": ab_id}))["identifier"]
            for ab_id in ab_ids
        ]

        # Stats
        pokemon_stats = await ctx.bot.db[1].pokemon_stats.find_one(
            {"pokemon_id": form_info["pokemon_id"]}
        )
        if not pokemon_stats:
            await ctx.send("That Pokemon does not exist!")
            return
        stats = pokemon_stats["stats"]
        pokemonSpeed = stats[5]
        pokemonSpd = stats[4]
        pokemonSpa = stats[3]
        pokemonDef = stats[2]
        pokemonAtk = stats[1]
        pokemonHp = stats[0]
        tlist = ", ".join(types)
        egg_groups = ", ".join(egg_groups)
        stats_str = (
            f"HP: {pokemonHp}\n"
            f"Attack: {pokemonAtk}\n"
            f"Defense: {pokemonDef}\n"
            f"Special Attack: {pokemonSpa}\n"
            f"Special Defense: {pokemonSpd}\n"
            f"Speed: {pokemonSpeed}"
        )

        # Evolution line / Catch Rate
        evo_line = ""
        catch_rate = ""
        form_suffix = form_info["form_identifier"]
        if form_suffix in ("alola", "galar", "hisui", "paldea"):
            form_suffix = ""
        base_name = val.lower().replace(form_suffix, "").strip("-")
        pfile = await ctx.bot.db[1].pfile.find_one({"identifier": base_name})
        gender_rate = pfile['gender_rate']
        if pfile is not None:
            raw_evos = (
                await ctx.bot.db[1]
                .pfile.find({"evolution_chain_id": pfile["evolution_chain_id"]})
                .to_list(None)
            )
            evo_line = await self.get_kids(raw_evos, None, "➥")
            evo_line = f"**Evolution Line**:\n{evo_line}"
            catch_rate = f"**Catch rate**: {pfile['capture_rate']}\n"

        # Weight
        weight = f'{form_info["weight"] / 10:.1f} kg'

        # Gender
        if gender_rate == -1:
            gender_txt = "Genderless"
        elif gender_rate == 0:
            gender_txt = "Male Only"
        elif gender_rate == 8:
            gender_txt = "Female Only"
        elif gender_rate == 1:
            gender_txt = "87.5% Male, 12.5% Female"
        elif gender_rate == 2:
            gender_txt = "75% Male, 25% Female"
        elif gender_rate == 4:
            gender_txt = "50% Male, 50% Female"
        elif gender_rate == 6:
            gender_txt = "25% Male, 75% Female"
        elif gender_rate == 7:
            gender_txt = "12.5% Male, 87.5% Female"

        if "arceus-" in val.lower():
            tlist = val.split("-")[1]
        emoji = get_emoji(
            shiny=shiny,
            skin=skin,
        )
        val = val.capitalize()
        embed = discord.Embed(
            title=f"{emoji}{val}", description="", color=random.choice(ctx.bot.colors)
        )
        abilities = ", ".join(abilities).capitalize()
        forms = forms.capitalize()
        embed.add_field(
            name="<:blank:1012504803496177685>",
            value=(
                f"**Abilities**: {abilities}\n"
                f"**Types**: {tlist}\n"
                f"**Egg Groups**: {egg_groups}\n"
                f"**Weight**: {weight}\n"
                f"**Gender Ratio**: {gender_txt}\n"
                f"{catch_rate}"
                f"**Stats**\n{stats_str}\n"
                f"**Available Forms**:\n{forms}\n"
                f"{evo_line}"
            ),
        )
        embed.set_footer(
            text=f"Evolve to any of the forms by using /form (form name) - Upvote MewBot"
        )
        embed.set_image(url=iurl)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="qi")
    @discord.app_commands.describe(
        pokemon="Can be <pokemon_number> | <pokemon_name> or 'new', 'latest' for most recent Pokémon or blank for currently selected Pokémon."
    )
    async def qinfo(self, ctx, pokemon: str = None):
        """Miniature version of the `info` command"""
        if pokemon is None:
            async with ctx.bot.db[0].acquire() as pconn:
                records = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT selected FROM users WHERE u_id = $1)",
                    ctx.author.id,
                )
            if records is None:
                await ctx.send(
                    f"You do not have a pokemon selected. Use `/select` to select one!"
                )
                return
            await ctx.send(embed=await get_pokemon_qinfo(ctx, records))
            return

        if pokemon in ("newest", "latest", "atest", "ewest", "new"):
            async with ctx.bot.db[0].acquire() as pconn:
                records = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT pokes[array_upper(pokes, 1)] FROM users WHERE u_id = $1)",
                    ctx.author.id,
                )
            await ctx.send(embed=await get_pokemon_qinfo(ctx, records))
            return

        try:
            pokemon = int(pokemon)
        except ValueError:
            pass
        else:
            if pokemon < 1:
                await ctx.send("That is not a valid pokemon number!")
                return
            async with ctx.bot.db[0].acquire() as pconn:
                records = await pconn.fetchrow(
                    "SELECT * FROM pokes WHERE id = (SELECT pokes[$1] FROM users WHERE u_id = $2)",
                    pokemon,
                    ctx.author.id,
                )
            if records is None:
                await ctx.send(
                    "You do not have that many pokemon. Go catch some more first!"
                )
                return
            await ctx.send(embed=await get_pokemon_qinfo(ctx, records))
            return

        # "pokemon" is *probably* a pokemon name
        pokemon = pokemon.lower().replace("alolan", "alola").split()
        shiny = "shiny" in pokemon
        radiant = "gleam" in pokemon
        if shiny:
            pokemon.remove("shiny")
        if radiant:
            pokemon.remove("gleam")
        pokemon = "-".join(pokemon)
        val = pokemon.capitalize()
        try:
            val = await self.parse_form(val)
            iurl = await get_pokemon_image(val, ctx.bot, shiny, radiant=radiant)
        except ValueError:
            await ctx.send("That Pokemon does not exist!")
            return
        forms = []
        if val.lower() in ("spewpa", "scatterbug"):
            forms = ["None"]
        else:
            # TODO: This is potentially VERY dangerous since this is user input directed to a regex pattern.
            cursor = ctx.bot.db[1].forms.find({"identifier": {"$regex": f".*{val}.*"}})
            forms = [t.capitalize() for t in await cursor.distinct("form_identifier")]
        forms = "\n".join(forms)

        form_info = await ctx.bot.db[1].forms.find_one({"identifier": val.lower()})
        if not form_info:
            await ctx.send("That Pokemon does not exist!")
            return
        ptypes = await ctx.bot.db[1].ptypes.find_one({"id": form_info["pokemon_id"]})
        if not ptypes:
            await ctx.send("That Pokemon does not exist!")
            return
        type_ids = ptypes["types"]
        types = [
            (await ctx.bot.db[1].types.find_one({"id": _type}))["identifier"]
            for _type in type_ids
        ]

        pokemon_stats = await ctx.bot.db[1].pokemon_stats.find_one(
            {"pokemon_id": form_info["pokemon_id"]}
        )
        if not pokemon_stats:
            await ctx.send("That Pokemon does not exist!")
            return
        stats = pokemon_stats["stats"]

        ab_ids = []
        async for record in ctx.bot.db[1].poke_abilities.find(
            {"pokemon_id": form_info["pokemon_id"]}
        ):
            ab_ids.append(record["ability_id"])
        ab_id = ab_ids[0]
        abilities = [
            (await ctx.bot.db[1].abilities.find_one({"id": ab_id}))["identifier"]
            for ab_id in ab_ids
        ]
        pokemonSpeed = stats[5]
        pokemonSpd = stats[4]
        pokemonSpa = stats[3]
        pokemonDef = stats[2]
        pokemonAtk = stats[1]
        pokemonHp = stats[0]
        tlist = ", ".join(types)

        if "arceus-" in val.lower():
            tlist = val.split("-")[1]
        emoji = get_emoji(
            shiny=shiny,
            radiant=radiant,
        )
        val = val.capitalize()
        embed = discord.Embed(
            title=f"{emoji}{val}", description="", color=random.choice(ctx.bot.colors)
        )
        abilities = ", ".join(abilities).capitalize()
        forms = forms.capitalize()
        embed.add_field(name="Types", value=f"`{tlist}`")
        embed.add_field(
            name="Base Stats",
            value=f"**HP:** `{pokemonHp}` | **Atk.:** `{pokemonAtk}` | **Def.:** `{pokemonDef}`\n**Sp.Atk.:** `{pokemonSpa}` | **Sp.Def.:** `{pokemonSpd}` | **Speed:** `{pokemonSpeed}`",
        )
        embed.set_footer(text="Quick information - Use /i for full info")
        # embed.set_image(url=iurl)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Pokemon(bot))
