import asyncpg
import asyncio
import random

from discord.ext import commands

from mewcogs.pokemon_list import *
from mewutils.misc import get_spawn_url, poke_spawn_check
from datetime import datetime
from math import floor


def is_key(item):
    conds = [item.endswith("-orb"), item == "coin-case"]
    return any(conds)


def getcap(level):
    if level <= 50:
        ans = (level**3 * (100 - level)) / 50
    elif level >= 50 and level <= 68:
        ans = (level**3 * (150 - level)) / 100
    elif level >= 68 and level <= 98:
        ans = (level**3 * ((1911 - 10 * level) / 3)) / 500
    elif level >= 98 and level <= 100:
        ans = (level**3 * (160 - level)) / 100
    else:
        ans = 2147483647
    ans = floor(ans // 10)
    ans = max(10, ans)
    return ans


def scatter(iterable):
    new_list = []
    for i in iterable:
        if random.randint(1, 2) == 1 and new_list.count("_") <= len(iterable) // 2:
            new_list.append("_")
        else:
            new_list.append(i)

    return " ".join(new_list)


class CatchView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context,
        pokemon: str,
        scattered_name: str,
        item: str,
        exp_gain: int,
        inventory: dict,
        shiny: bool,
    ):
        self.modal = FishingSpawnModal(
            pokemon, scattered_name, item, exp_gain, inventory, shiny, self
        )
        super().__init__(timeout=60)
        self.ctx = ctx
        self.msg = None

    def set_message(self, msg: discord.Message):
        self.msg = msg

    async def on_timeout(self):
        if self.msg:
            embed = self.msg.embeds[0]
            embed.title = "Timed out!"
            embed.description = "It got away! Better luck next time..."
            await self.msg.edit(embed=embed, view=None)

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(
        label="What Pokemon might this be!", style=discord.ButtonStyle.blurple
    )
    async def click_here(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(self.modal)


class FishingSpawnModal(discord.ui.Modal, title="Catch This Pokemon!"):
    def __init__(
        self,
        pokemon: str,
        scattered_name: str,
        item: str,
        exp_gain: int,
        inventory: dict,
        shiny: bool,
        view: discord.ui.View,
    ):
        self.pokemon = pokemon
        self.scattered_name = scattered_name
        self.guessed = False
        self.item = item
        self.exp_gain = exp_gain
        self.inventory = inventory
        self.shiny = shiny
        self.view = view
        super().__init__()

    name = discord.ui.TextInput(
        label=f"Pokemon Name", placeholder="What do you think this Pokemon is?!"
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.embedmsg = interaction.message

        await interaction.response.defer()

        pokemon = self.pokemon
        item = self.item
        shiny = self.shiny
        exp_gain = self.exp_gain
        exp = self.inventory["fishing_exp"]
        level = self.inventory["fishing_level"]
        energy = self.inventory["energy"]
        cap = self.inventory["fishing_level_cap"]
        rod = self.inventory["held_item"].replace("-", " ")

        # Check if pokemon name is correct
        if self.guessed:
            return await interaction.followup.send(
                "Someone's already guessed this pokemon!", ephemeral=True
            )

        if interaction.client.botbanned(interaction.user.id) or not poke_spawn_check(
            str(self.name), pokemon
        ):
            btn = self.view.children[0]
            btn.disabled = True
            btn.style = discord.ButtonStyle.secondary
            self.view.stop()
            embed = self.embedmsg.embeds[0]
            embed.title = f"The {pokemon} escaped."
            embed.description = ""
            embed.set_footer(
                text=f"You have lost an Energy Point - You have {energy-1} remaining!"
            )
            return await self.embedmsg.edit(embed=embed, view=self.view)

        # Someone caught the poke, create it
        pokedata = await interaction.client.commondb.create_poke(
            interaction.client, interaction.user.id, pokemon, shiny=shiny
        )
        ivpercent = round((pokedata.iv_sum / 186) * 100, 2)
        async with interaction.client.db[0].acquire() as pconn:
            if item not in ("common chest", "rare chest"):
                items = await pconn.fetchval(
                    "SELECT items::json FROM users WHERE u_id = $1", interaction.user.id
                )
                items[item] = items.get(item, 0) + 1
                await pconn.execute(
                    "UPDATE users SET items = $1::json WHERE u_id = $2",
                    items,
                    interaction.user.id,
                )
            else:
                inventory = await pconn.fetchval(
                    "SELECT inventory::json FROM users WHERE u_id = $1",
                    interaction.user.id,
                )
                inventory[item] = inventory.get(item, 0) + 1
                await pconn.execute(
                    "UPDATE users SET inventory = $1::json where u_id = $2",
                    inventory,
                    interaction.user.id,
                )
            leveled_up = cap < (exp_gain + exp) and level < 100
            if leveled_up:
                newcap = getcap(level)
                level += 1
                await pconn.execute(
                    f"UPDATE users SET fishing_level = $3, fishing_level_cap = $2, fishing_exp = 0 WHERE u_id = $1",
                    interaction.user.id,
                    newcap,
                    level,
                )
            else:
                await pconn.execute(
                    f"UPDATE users SET fishing_exp = fishing_exp + $2 WHERE u_id = $1",
                    interaction.user.id,
                    exp_gain,
                )

        e = discord.Embed(
            title=f"Here's what you got from fishing with your {rod}!",
            color=0xFFB6C1,
        )
        item = item.replace("-", " ").capitalize()
        e.add_field(
            name="You caught a", value=f"{pokedata.emoji}{pokemon} ({ivpercent}% iv)!"
        )
        e.add_field(name="You also found a", value=f"{item}")
        e.add_field(
            name=f"You also got {exp_gain} Fishing Experience Points",
            value="Increase your fishing Exp gain by buying a Better Rod!",
        )
        if leveled_up:
            e.add_field(
                name="You also Leveled Up!",
                value=f"Your Fishing Level is now Level {level}",
            )

        e.set_footer(
            text=f"You have lost an Energy Point - You have {energy-1} remaining!"
        )
        #
        user = await interaction.client.mongo_find(
            "users",
            {"user": interaction.user.id},
            default={"user": interaction.user.id, "progress": {}},
        )
        progress = user["progress"]
        progress["fish"] = progress.get("fish", 0) + 1
        await interaction.client.mongo_update(
            "users", {"user": interaction.user.id}, {"progress": progress}
        )
        #
        try:
            await self.embedmsg.edit(embed=e, view=None)
        except discord.NotFound:
            await interaction.channel.send(embed=e)
        if energy <= 0:
            await interaction.channel.send(
                "You have used up all your Energy!\nWait for your Energy to be replenished, or vote for Mewbot to get more energy!"
            )
            cog = interaction.client.get_cog("Extras")
            if cog is not None:
                await cog.vote.callback(cog, ctx)

        self.guessed = True
        self.view.stop()
        # Dispatches an event that a poke was fished.
        # on_poke_fish(self, channel, user)
        interaction.client.dispatch("poke_fish", interaction.channel, interaction.user)


class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def fish(self, ctx):
        """Play the Fishing Minigame and get Pokémon"""
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT *, inventory::json as cast_inv FROM users WHERE u_id = $1",
                ctx.author.id,
            )
        if details is None:
            await ctx.send("You have not started!\nStart with `/start` first.")
            return
        rod = details["held_item"]
        if not rod or not rod.endswith("rod"):
            await ctx.send(
                "You are not Holding a Fishing Rod!\nBuy one in the shop with `/shop rods` first."
            )
            return
        rod = rod.capitalize().replace("-", " ")
        exp = details["fishing_exp"]
        level = details["fishing_level"]
        energy = details["energy"]
        cap = details["fishing_level_cap"]

        if energy <= 0:
            await ctx.send(
                "You don't have any more energy points!\nWait for your Energy to be replenished, or vote for Mewbot to get more energy!"
            )
            cog = ctx.bot.get_cog("Extras")
            if cog is not None:
                await cog.vote.callback(cog, ctx)
            return
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                f"UPDATE users SET energy = energy - 1 WHERE u_id = $1",
                ctx.author.id,
            )
        energy = energy - 1

        e = discord.Embed(title=f"You Cast Your {rod} into the Water!", color=0xFFB6C1)
        e.add_field(name="Fishing", value="...")
        e.set_image(url=await get_spawn_url("fishing.gif"))
        embed = await ctx.send(embed=e)

        SHOP = await ctx.bot.db[1].shop.find({}).to_list(None)
        cheaps = [
            t["item"]
            for t in SHOP
            if t["price"] <= 3500
            and not is_key(t["item"])
            and not t["item"] == "old-rod"
        ]
        mids = [
            t["item"]
            for t in SHOP
            if t["price"] >= 3500
            and t["price"] <= 5000
            and not is_key(t["item"])
            and not t["item"] == "old-rod"
        ]
        expensives = [
            t["item"]
            for t in SHOP
            if t["price"] >= 5000
            and t["price"] <= 8000
            and not is_key(t["item"])
            and not t["item"] == "old-rod"
        ]
        supers = [
            t["item"]
            for t in SHOP
            if t["price"] >= 8000
            and not is_key(t["item"])
            and not t["item"] == "old-rod"
        ]

        # Fishing EXP bonuses cap at level 100, RNG from [0...2000] to 10000 (20%)
        chance = random.uniform(max(min(100, level), 0) * 20, 10000)
        if chance < 8000:  # 80%
            item = random.choice(cheaps)
            poke = random.choice(common_water)
        elif chance < 9500:  # 15%
            item = random.choice(cheaps)
            poke = random.choice(uncommon_water)
        elif chance < 9900:  # 4%
            item = random.choice(mids)
            poke = random.choice(rare_water)
        elif chance < 9999:  # 0.99%
            item = random.choice(expensives)
            poke = random.choice(extremely_rare_water)
        else:  # 0.01%
            item = random.choice(supers)
            poke = random.choice(ultra_rare_water)
        poke = poke.capitalize()

        # chance to get chests
        if not random.randint(0, 50):
            item = "common chest"
        elif not random.randint(0, 400):
            item = "rare chest"

        # SMALL chance to get an ultra rare item 3/10000 -> 15/10000
        chance = random.uniform(0, 10000)
        chance -= min(exp, 100000) / 8333
        if chance < 3:
            item = random.choice(("rusty-sword", "rusty-shield"))

        pkid = (await ctx.bot.db[1].forms.find_one({"identifier": poke.lower()}))[
            "pokemon_id"
        ]
        name = poke
        threshold = 8000

        inventory = details["cast_inv"]
        threshold = round(
            threshold - threshold * (inventory.get("shiny-multiplier", 0) / 100)
        )
        shiny = random.choice([False for i in range(threshold)] + [True])
        exp_gain = [
            t["price"] for t in SHOP if t["item"] == rod.lower().replace(" ", "-")
        ][0] / 1000
        exp_gain += exp_gain * level / 2

        await asyncio.sleep(random.randint(3, 7))
        scattered_name = scatter(name)
        e = discord.Embed(title=f"You have encountered a **`{scattered_name}`**")
        e.set_footer(text="You have 15 Seconds to guess the Pokemon to catch it!")
        try:
            view = CatchView(
                ctx=ctx,
                pokemon=poke,
                scattered_name=scattered_name,
                item=item,
                inventory=details,
                exp_gain=exp_gain,
                shiny=shiny,
            )
            await embed.edit(embed=e, view=view)

            view.set_message(embed)

        except discord.NotFound:
            await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Fishing(bot))
