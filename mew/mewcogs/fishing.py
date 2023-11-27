import discord
import asyncpg
import asyncio
import random
import time

from discord import app_commands
from discord.ext import commands
from datetime import datetime
from math import floor
from time import perf_counter
from random import shuffle

from mewcogs.pokemon_list import *
from mewutils.misc import get_spawn_url, poke_spawn_check


def do_health(maxHealth, health, healthDashes=10):
    dashConvert = int(
        maxHealth / healthDashes
    )  # Get the number to divide by to convert health to dashes (being 10)
    currentDashes = int(
        health / dashConvert
    )  # Convert health to dash count: 80/10 => 8 dashes
    remainingHealth = (
        healthDashes - currentDashes
    )  # Get the health remaining to fill as space => 12 spaces
    cur = f"{round(health)}/{maxHealth}"

    healthDisplay = "".join(
        ["▰" for i in range(currentDashes)]
    )  # Convert 8 to 8 dashes as a string:   "--------"
    remainingDisplay = "".join(
        ["▱" for i in range(remainingHealth)]
    )  # Convert 12 to 12 spaces as a string: "            "
    percent = floor(
        (health / maxHealth) * 100
    )  # Get the percent as a whole number:   40%
    if percent < 1:
        percent = 0
    return f"{healthDisplay}{remainingDisplay}\n           {cur}"  # Print out textbased healthbar


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
        name_being_guessed: str,
        item: str,
        exp_gain: int,
        inventory: dict,
        shiny: bool,
        start_time: float,
        activity: str,
        held_item: str,
    ):
        self.modal = ActivitySpawnModal(
            pokemon,
            name_being_guessed,
            item,
            exp_gain,
            inventory,
            shiny,
            start_time,
            activity,
            held_item,
            self,
        )
        super().__init__(timeout=30)
        self.ctx = ctx
        self.msg = None
        self.pokemon = pokemon

    def set_message(self, msg: discord.Message):
        self.msg = msg

    async def on_timeout(self):
        if self.msg:
            embed = self.msg.embeds[0]
            embed.title = "Timed out!"
            embed.description = (
                f"**{self.pokemon.capitalize()}** got away! Better luck next time..."
            )
            await self.msg.edit(embed=embed, view=None)
            return

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(
        label="What Pokemon might this be!", style=discord.ButtonStyle.blurple
    )
    async def click_here(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(self.modal)


class ActivitySpawnModal(discord.ui.Modal, title="Catch This Pokemon!"):
    def __init__(
        self,
        pokemon: str,
        name_being_guessed: str,
        item: str,
        exp_gain: int,
        inventory: dict,
        shiny: bool,
        start_time: float,
        activity: str,
        held_item: str,
        view: discord.ui.View,
    ):
        self.pokemon = pokemon
        self.name_being_guessed = name_being_guessed
        self.guessed = False
        self.item = item
        self.exp_gain = exp_gain
        self.inventory = inventory
        self.shiny = shiny
        self.start_time = start_time
        self.activity = activity
        self.held_item = held_item
        self.view = view
        self.attempts = 1
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
        activity = self.activity
        exp_gain = self.exp_gain
        energy = self.inventory["energy"]

        # Depends on activity
        if activity == "fishing":
            exp = self.inventory["fishing_exp"]
            level = self.inventory["fishing_level"]
            cap = self.inventory["fishing_level_cap"]
        else:
            exp = self.inventory["mining_exp"]
            level = self.inventory["mining_level"]
            cap = self.inventory["mining_level_cap"]
        item_msg = ""

        # Check if pokemon name is correct
        if self.guessed:
            return await interaction.followup.send(
                "Someone's already guessed this pokemon!", ephemeral=True
            )

        # Leave original Botban code in
        if interaction.client.botbanned(interaction.user.id):
            btn = self.view.children[0]
            btn.disabled = True
            btn.style = discord.ButtonStyle.secondary
            self.view.stop()
            embed = self.embedmsg.embeds[0]
            embed.title = f"The {pokemon} escaped."
            embed.description = f"Lost an Energy Point - {energy-1} remaining!"
            # embed.set_footer(text=f"Lost an Energy Point - {energy-1} remaining!")
            return await self.embedmsg.edit(embed=embed, view=self.view)

        # Added multiple attempts. So Users should get 2 tries towards the name.
        if not poke_spawn_check(str(self.name), pokemon) and self.attempts > 2:
            btn = self.view.children[0]
            btn.disabled = True
            btn.style = discord.ButtonStyle.secondary
            self.view.stop()
            embed = self.embedmsg.embeds[0]
            embed.title = f"The {pokemon} escaped."
            embed.description = f"Lost an Energy Point - {energy-1} remaining!"
            # embed.set_footer(text=f"Lost an Energy Point - {energy-1} remaining!")
            return await self.embedmsg.edit(embed=embed, view=self.view)
        elif not poke_spawn_check(str(self.name), pokemon) and self.attempts >= 0:
            self.attempts += 1
            return await interaction.followup.send(
                "Incorrect name! Try again.", ephemeral=True
            )
        else:
            pass

        # Someone caught the poke, create it
        pokedata = await interaction.client.commondb.create_poke(
            interaction.client, interaction.user.id, pokemon, shiny=shiny
        )
        ivpercent = round((pokedata.iv_sum / 186) * 100, 2)

        async with interaction.client.db[0].acquire() as pconn:
            # Handle points
            end_time = perf_counter()
            final_time = round(end_time - self.start_time)

            if final_time >= 1 and final_time <= 5:
                newPoints = random.randint(10, 15)
            elif final_time >= 6 and final_time <= 10:
                newPoints = random.randint(5, 10)
            elif final_time >= 11 and final_time <= 15:
                newPoints = random.randint(1, 5)
            else:
                newPoints = random.randint(1, 5)

            if activity == "fishing":
                await pconn.execute(
                    "UPDATE users SET fishing_points = fishing_points + $1 WHERE u_id = $2",
                    newPoints,
                    interaction.user.id,
                )
            else:
                await pconn.execute(
                    "UPDATE users SET mining_points = mining_points + $1 WHERE u_id = $2",
                    newPoints,
                    interaction.user.id,
                )

            # Credit Reward - Only Fishing
            if type(item) is int and activity == "fishing":
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                    item,
                    interaction.user.id,
                )
                item_msg = f"**{item}** credits"

            # Radiant Gems - Only Mining
            elif type(item) is int and activity == "mining":
                await interaction.client.commondb.add_bag_item(
                    interaction.user.id, "radiant_gem", item, True
                )
                item_msg = f"**{item}** Gleam Gems"

            # Item/Chest Reward
            else:
                # Chest, Gleam Gems are Account Bound items
                if item not in ("common_chest", "rare_chest"):
                    bound = False
                else:
                    bound = True

                # TODO:Can be removed once spelling is right in pokemon_list.py
                if item == "poison_bard":
                    item = "poison_barb"
                print(item)
                await interaction.client.commondb.add_bag_item(
                    interaction.user.id, item, 1, bound
                )

                # If we pass a credit here it errors. Only done during battle items or chest
                item = item.replace("_", " ").title()
                item_msg = f"**{item}**"

            # Exp rewards
            leveled_up = cap < (exp_gain + exp) and level < 100
            if leveled_up:
                newcap = getcap(level)
                level += 1
                if activity == "fishing":
                    await pconn.execute(
                        f"UPDATE users SET fishing_level = $3, fishing_level_cap = $2, fishing_exp = 0 WHERE u_id = $1",
                        interaction.user.id,
                        newcap,
                        level,
                    )
                else:  # Mining
                    await pconn.execute(
                        f"UPDATE users SET mining_level = $3, mining_level_cap = $2, mining_exp = 0 WHERE u_id = $1",
                        interaction.user.id,
                        newcap,
                        level,
                    )
            else:
                if activity == "fishing":
                    await pconn.execute(
                        f"UPDATE users SET fishing_exp = fishing_exp + $2 WHERE u_id = $1",
                        interaction.user.id,
                        exp_gain,
                    )
                else:  # Mining
                    await pconn.execute(
                        f"UPDATE users SET mining_exp = mining_exp + $2 WHERE u_id = $1",
                        interaction.user.id,
                        exp_gain,
                    )

        # Start embed
        e = discord.Embed(
            title=f"{activity.capitalize()} Complete!",
            description=f"Here's what you got from {activity} with your **{self.held_item.title()}**!",
            color=0xFFB6C1,
        )
        # Caught pokemon and item
        e.add_field(
            name="Rewards!",
            value=f"`Caught`: {pokedata.emoji}{pokemon} - {ivpercent}% IV\n`Item`: {item_msg}",
            inline=True,
        )
        # Handle exp gain
        exp_msg = (
            f"`{activity.capitalize()} Points`: {newPoints}\n`Exp Gain`: {exp_gain} exp"
        )
        if leveled_up:
            exp_msg += f"\nLeveled up!\nYour {activity.capitalize()} Level is now **Level {level}**!"
        e.add_field(
            name=f"{activity.capitalize()} Skill", value=f"{exp_msg}", inline=True
        )
        e.set_footer(
            text=f"Lost an Energy Point - {energy-1} remaining! | Took {final_time} secs."
        )
        # Only if fishing
        if activity == "fishing":
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

        self.guessed = True
        self.view.stop()
        # Dispatches an event that a poke was fished.
        # on_poke_fish(self, channel, user)
        # TODO: Update bottom event for event orientated fishing events
        # interaction.client.dispatch("poke_fish", interaction.channel, interaction.user)


class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def mg(self, ctx):
        """
        Minigame command
        """
        pass

    @mg.command()
    async def fish(self, ctx):
        """Provides Battle Items and Pokemon"""
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
                    "You are not Holding a Fishing Rod!\nBuy one in the shop with `/shop minigames` first.\nIf currently own one, unequip it and then equip it again!"
                )
                return
            rod = rod.capitalize().replace("-", " ")
            level = details["fishing_level"]

            # Handle energy
            energy = details["energy"]
            if energy <= 0:
                await ctx.send(
                    "You don't have any more energy points!\nWait for your Energy to be replenished, or vote for Mewbot to get more energy!"
                )
                cog = ctx.bot.get_cog("Extras")
                if cog is not None:
                    await cog.vote.callback(cog, ctx)
                return
            await pconn.execute(
                f"UPDATE users SET energy = energy - 1 WHERE u_id = $1",
                ctx.author.id,
            )
            energy = energy - 1

            # Initial embed
            e = discord.Embed(
                title=f"Let's go Fishing",
                description=f"You cast your {rod.title()} into the water!",
                color=0xFFBC61,
            )
            e.set_image(url="https://mewbot.xyz/poke-fish.gif")
            embed = await ctx.send(embed=e)

            # Added two different chances for items and fish
            # This could be changed to reflect rarity for BOTH
            fish_chance = random.choices(
                ("common", "uncommon", "uncommon", "extreme_rare"),
                weights=(0.59, 0.20, 0.15, 0.05),
            )[0]

            if fish_chance == "common":
                poke = random.choice(common_water)
            elif fish_chance == "uncommon":
                poke = random.choice(uncommon_water)
            elif fish_chance == "rare":
                poke = random.choice(rare_water)
            elif fish_chance == "extreme_rare":
                poke = random.choice(extremely_rare_water)
            poke = poke.capitalize()

            item_chance = random.choices(
                ("credits", "item", "common_chest", "rare_chest"),
                weights=(0.440, 0.36, 0.15, 0.05),
            )[0]
            if item_chance == "credits":
                item = random.randint(5000, 10000)
            elif item_chance == "item":
                item = random.choice(battle_items)
            elif item_chance == "common_chest":
                item = "common_chest"
            elif item_chance == "rare_chest":
                item = "rare_chest"

            name = poke

            # If Fishing Lvl 100 set threshold to normal
            if level >= 100:
                threshold = 4000
            else:
                threshold = 8000

            inventory = details["cast_inv"]
            threshold = round(
                threshold - threshold * (inventory.get("shiny-multiplier", 0) / 100)
            )
            shiny = random.choice([False for i in range(threshold)] + [True])

            SHOP = await ctx.bot.db[1].new_shop.find({}).to_list(None)
            exp_gain = [
                t["price"] for t in SHOP if t["item"] == rod.lower().replace(" ", "_")
            ][0] / 1000
            # If Rod isn't Super or Ultra reduce exp gain by 50%
            if rod not in ("super rod", "ultra rod"):
                exp_gain += exp_gain * level / 2

            await asyncio.sleep(random.randint(3, 7))
            scattered_name = scatter(name)

            if ctx.author.id == 334155028170407949:
                await ctx.send(f"{name}")

            # Resend embed with scrambled name
            e = discord.Embed(
                title=f"Something bit your hook!",
                description=f"You've encountered `{scattered_name}`",
                color=0xFFBC61,
            )
            e.set_image(url="https://mewbot.xyz/poke-fish.gif")
            e.set_footer(
                text=f"You have 30 secs to guess the Pokemon to catch it.",
                # icon_url = ctx.author.avatar_url
            )
            try:
                # Start timer
                start_time = perf_counter()

                view = CatchView(
                    ctx=ctx,
                    pokemon=poke,
                    name_being_guessed=scattered_name,
                    item=item,
                    inventory=details,
                    exp_gain=exp_gain,
                    shiny=shiny,
                    start_time=start_time,
                    activity="fishing",
                    held_item=rod,
                )

                await embed.edit(embed=e, view=view)

                view.set_message(embed)
            except discord.NotFound:
                await ctx.send(embed=e)

    @mg.command()
    async def mine(self, ctx):
        """Provides Crystals and Pokemon"""
        async with ctx.bot.db[0].acquire() as pconn:
            details = await pconn.fetchrow(
                "SELECT *, inventory::json as mine_inv FROM users WHERE u_id = $1",
                ctx.author.id,
            )
            if details is None:
                await ctx.send("You have not started!\nStart with `/start` first.")
                return
            shovel = details["shovel"]
            if not shovel or not shovel.endswith("shovel"):
                await ctx.send(
                    "You are not holding a Shovel!\nBuy one in the shop with `/shop minigames` first."
                )
                return
            shovel = shovel.capitalize().replace("_", " ")
            level = details["mining_level"]

            # Handle energy
            energy = details["energy"]
            if energy <= 0:
                await ctx.send(
                    "You don't have any more energy points!\nWait for your Energy to be replenished, or vote for Mewbot to get more energy!"
                )
                cog = ctx.bot.get_cog("Extras")
                if cog is not None:
                    await cog.vote.callback(cog, ctx)
                return
            await pconn.execute(
                f"UPDATE users SET energy = energy - 1 WHERE u_id = $1",
                ctx.author.id,
            )
            energy = energy - 1

            # Initial embed
            chance = random.uniform(1000, 10000)
            e = discord.Embed(
                title=f"Let's go Mining",
                description=f"You start digging with your **{shovel.title()}**!",
                color=0xFFBC61,
            )
            e.set_image(url="https://mewbot.xyz/mining.png")
            embed = await ctx.send(embed=e)

            # Added two different chances for items and fish
            # This could be changed to reflect rarity for BOTH
            fish_chance = random.choices(
                ("common", "uncommon", "uncommon", "extreme_rare"),
                weights=(0.59, 0.20, 0.15, 0.05),
            )[0]

            if fish_chance == "common":
                poke = random.choice(common_mining)
            elif fish_chance == "uncommon":
                poke = random.choice(uncommon_mining)
            elif fish_chance == "rare":
                poke = random.choice(rare_mining)
            elif fish_chance == "extreme_rare":
                poke = random.choice(extremely_rare_mining)
            poke = poke.capitalize()

            item_chance = random.choices(
                ("radiant_gem", "item", "common_chest", "rare_chest"),
                weights=(0.25, 0.50, 0.17, 0.03),
            )[0]
            if item_chance == "radiant_gem":
                item = random.randint(2, 8)
            elif item_chance == "item":
                item = random.choice(crystals)
            elif item_chance == "common_chest":
                item = "common_chest"
            elif item_chance == "rare_chest":
                item = "rare_chest"

            name = poke

            # If Mining Lvl 100 set threshold to normal
            if level >= 100:
                threshold = 4000
            else:
                threshold = 8000

            inventory = details["mine_inv"]
            threshold = round(
                threshold - threshold * (inventory.get("shiny-multiplier", 0) / 100)
            )
            shiny = random.choice([False for i in range(threshold)] + [True])

            SHOP = await ctx.bot.db[1].new_shop.find({}).to_list(None)
            exp_gain = [
                t["price"]
                for t in SHOP
                if t["item"] == shovel.lower().replace(" ", "_")
            ][0] / 1000
            # If Rod isn't Super or Ultra reduce exp gain by 50%
            if shovel not in ("super shovel", "ultra shovel"):
                exp_gain += exp_gain * level / 2

            await asyncio.sleep(random.randint(3, 7))
            # scattered_name = scatter(name)
            letter_list = list(name)
            shuffle(letter_list)
            provided_name = "".join(letter_list)

            if ctx.author.id == 334155028170407949:
                await ctx.send(f"{name}")

            # Resend embed with scrambled name
            e = discord.Embed(
                title=f"Your **{shovel.title()}** hit something!",
                description=f"You've encountered `{provided_name}`",
                color=0xFFBC61,
            )
            e.set_image(url="https://mewbot.xyz/mining_active.gif")
            e.set_footer(
                text=f"You have 30 secs to guess the Pokemon to catch it.",
                # icon_url = ctx.author.avatar_url
            )
            try:
                # Start timer
                start_time = perf_counter()

                view = CatchView(
                    ctx=ctx,
                    pokemon=poke,
                    name_being_guessed=provided_name,
                    item=item,
                    inventory=details,
                    exp_gain=exp_gain,
                    shiny=shiny,
                    start_time=start_time,
                    activity="mining",
                    held_item=shovel,
                )

                await embed.edit(embed=e, view=view)

                view.set_message(embed)
            except discord.NotFound:
                await ctx.send(embed=e)

    # Moved to minigames b/c it's mainly used in relation to this.
    @commands.hybrid_command()
    async def energy(self, ctx):
        """Energy and Minigame info"""
        async with ctx.bot.db[0].acquire() as tconn:
            details = await tconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", ctx.author.id
            )
            fishing_players = await tconn.fetch(
                f"SELECT u_id, fishing_points FROM users WHERE fishing_points != 0 ORDER BY fishing_points DESC"
            )
            mining_players = await tconn.fetch(
                f"SELECT u_id, mining_points FROM users WHERE mining_points != 0 ORDER BY mining_points DESC"
            )
            fishing_ids = [record["u_id"] for record in fishing_players]
            mining_ids = [record["u_id"] for record in mining_players]

        if details is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            return
        embed = discord.Embed(
            title="Your Energy",
            description="Different stats and levels from various minigames!",
            color=0xFFB6C1,
        )
        fishing_level = details["fishing_level"]
        fishing_exp = details["fishing_exp"]
        fishing_levelcap = details["fishing_level_cap"]
        fishing_points = details["fishing_points"]
        mining_level = details["mining_level"]
        mining_exp = details["mining_exp"]
        mining_levelcap = details["mining_level_cap"]
        mining_points = details["mining_points"]
        mg_energy = do_health(10, details["energy"])
        npc_energy = do_health(10, details["npc_energy"])

        if ctx.author.id in fishing_ids:
            fishing_position = fishing_ids.index(ctx.author.id)
            position_msg = f"`Position`: {fishing_position + 1}"
        else:
            position_msg = "`Position`: Not Rated"

        if ctx.author.id in mining_ids:
            mining_position = mining_ids.index(ctx.author.id)
            mining_position_msg = f"`Position`: {mining_position + 1}"
        else:
            mining_position_msg = "`Position`: Not Rated"

        embed.add_field(
            name="Minigame Info",
            value=(
                f"__**Fishing Stats**__ 🐟\n`Level`: {fishing_level} - `Exp`: {fishing_exp}/{fishing_levelcap}\n`Points`: {fishing_points} - {position_msg}\n"
                f"__**Mining Stats**__ <:shovel:1083508753065848994>\n`Level`: {mining_level} - `Exp`: {mining_exp}/{mining_levelcap}\n`Points`: {mining_points} - {mining_position_msg}"
            ),
        )

        embed.add_field(
            name="Energy Levels",
            value=(
                f"__**Minigame Energy**__\n{mg_energy}\n"
                f"__**NPC Energy**__\n{npc_energy}"
            ),
        )

        embed.set_footer(text="If you have some Energy go fishing or mining!")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Minigames(bot))
