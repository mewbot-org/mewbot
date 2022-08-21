import discord
import asyncio
import asyncpg

from discord.ext import commands

from mewutils.misc import get_emoji, pagify, MenuView, AsyncIter


class Favs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def fav_list(self, ctx):
        await ctx.send(
            "This command is deprecated, you should use `/f p args:fav` instead. "
            "It has the same functionality, but with a fresh output and the ability to use additional filters.\n"
            "Running that for you now..."
        )
        await asyncio.sleep(3)
        c = ctx.bot.get_cog("Filter")
        if c is None:
            return
        await c.filter_pokemon.callback(c, ctx, args="fav")
        return

        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT pokes, user_order FROM users WHERE u_id = $1", ctx.author.id
            )
        if details is None:
            await ctx.send("You have not started!\nStart with `/start` first.")
            return
        pokes, user_order = details

        orders = {
            "iv": "ORDER by ivs DESC",
            "level": "ORDER by pokelevel DESC",
            "ev": "ORDER by evs DESC",
            "name": "order by pokname DESC",
            "kek": "",
        }
        order = orders.get(user_order)
        query = f"""SELECT *, COALESCE(atkiv,0) + COALESCE(defiv,0) + COALESCE(spatkiv,0) + COALESCE(spdefiv,0) + COALESCE(speediv,0) + COALESCE(hpiv,0) AS ivs, COALESCE(atkev,0) + COALESCE(defev,0) + COALESCE(spatkev,0) + COALESCE(spdefev,0) + COALESCE(speedev,0) + COALESCE(hpev,0) AS evs FROM pokes WHERE id = ANY ($1) AND fav = True {order}"""
        async with ctx.bot.db[0].acquire() as pconn:
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
                blank="<:blank:942623726715936808>",
                shiny=shiny,
                radiant=radiant,
                skin=record["skin"],
            )
            gender = ctx.bot.misc.get_gender_emote(record["gender"])
            desc += f'{emoji}{gender}**{nr.capitalize()}** | **__No.__** - {pn} | **Level** {level} | **IV%** {iv/186:.2%}\n'

        embed = discord.Embed(title="Your Pokemon", color=0xFFB6C1)
        pages = pagify(desc, base_embed=embed)
        await MenuView(ctx, pages).start()

    @commands.hybrid_command()
    async def fav_add(self, ctx, poke: int=None):
        async with ctx.bot.db[0].acquire() as pconn:
            if poke is None:
                _id = await pconn.fetchval(
                    "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
                )
            else:
                if poke < 1:
                    await ctx.send("You don't have that Pokemon")
                    return
                _id = await pconn.fetchval(
                    "SELECT pokes[$1] FROM users WHERE u_id = $2",
                    poke,
                    ctx.author.id,
                )
            name = await pconn.fetchval("SELECT pokname FROM pokes WHERE id = $1", _id)
            if name is None:
                await ctx.send("You don't have that Pokemon")
                return
            await pconn.execute("UPDATE pokes SET fav = $1 WHERE id = $2", True, _id)
            await ctx.send(
                f"You have successfully added your {name} to your favourite pokemon list!"
            )

    @commands.hybrid_command()
    async def fav_remove(self, ctx, poke: int=None):
        async with ctx.bot.db[0].acquire() as pconn:
            if poke is None:
                _id = await pconn.fetchval(
                    "SELECT selected FROM users WHERE u_id = $1", ctx.author.id
                )
            else:
                if poke < 1:
                    await ctx.send("You don't have that Pokemon")
                    return
                _id = await pconn.fetchval(
                    "SELECT pokes[$1] FROM users WHERE u_id = $2",
                    poke,
                    ctx.author.id,
                )
            name = await pconn.fetchval("SELECT pokname FROM pokes WHERE id = $1", _id)
            if name is None:
                await ctx.send("You don't have that Pokemon")
                return
            await pconn.execute("UPDATE pokes SET fav = $1 WHERE id = $2", False, _id)
            await ctx.send(
                f"You have successfully removed your {name} from your favourite pokemon list!"
            )

async def setup(bot):
    await bot.add_cog(Favs(bot))
