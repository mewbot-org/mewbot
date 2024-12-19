import time
import discord
import random
import asyncio

from mewcogs.json_files import make_embed


from discord.ext import commands
from typing import Literal
from mewcogs.pokemon_list import (
    pList,
    LegendList,
    natlist,
    pseudoList,
    ubList,
    starterList,
    totalList,
)
from mewutils.misc import ConfirmView, ListSelectView


class Chests(commands.Cog):
    """Open and view info on Radiant Chests."""

    def __init__(self, bot):
        self.bot = bot
        # currently available gleam pokemon, ("Pokemon")
        self.CURRENTLY_ACTIVE = [
            "Onix",
            "Cyclizar",
            "Cryogonal",
            "Brute-bonnet",
            "Regieleki",
            "Calyrex",
            "Pawmi",
            "Swinub",
            "Nacli",
            "Mareep",
        ]

        # currently available event radiants, {"Pokemon": "String when they get that poke!\n"}
        self.EVENT_ACTIVE = {}
        # packs that can be bought with ;radiant, (("Pack Desc", <int - Price in radiant gems>))
        self.PACKS = (
            ("Shiny Multiplier x1", 5),
            ("Battle Multiplier x1", 5),
            ("IV Multiplier x1", 5),
            ("Breeding Multiplier x1", 5),
            ("Legend Chest", 75),
            ("Gleam Pokemon (common & starter)", 150),
            ("Gleam Pokemon (legend & pseudo)", 300),
        )
        self.CREDITS_PER_MULTI = 100000
        legend = set(LegendList + ubList + pseudoList)
        common = set(pList + starterList) - legend
        self.LEGEND = set(self.CURRENTLY_ACTIVE) & legend
        self.COMMON = set(self.CURRENTLY_ACTIVE) & common
        self.purchaselock = []

        self.CHEST_DATA = {
            "COMMON": {
                "rewards": [
                    ("gems", 0.2, "Basic gems to fuel your adventures!"),
                    ("credits", 0.3, "Earn credits to spend on various in-game perks."),
                    (
                        "shadowstreak",
                        0.15,
                        "A mysterious streak of shadow energy that powers your adventures!",
                    ),
                    (
                        "rare_chest",
                        0.3,
                        "A mysterious chest with rare treasures. Only for the daring!",
                    ),
                    (
                        "mythic_chest",
                        0.05,
                        "A chest containing higher-tier items and legendary treasures!",
                    ),
                ],
                "description": "A simple chest with modest rewards. Perfect for casual trainers.",
                "emoji": "📦",
                "color": discord.Color.green(),
                "image_url": "https://media.discordapp.net/attachments/1301161012656869438/1311618583637528576/75_Sem_Titulo_20241128060125.png?ex=6749837f&is=674831ff&hm=a45af0d8cb1e0cbe0f2ebb7b59babcd6c6567da358f0f33a80f0ae69188d77c9&=&format=webp&quality=lossless&width=88&height=88",
            },
            "RARE": {
                "rewards": [
                    ("gems", 0.2, "Basic gems to fuel your adventures!"),
                    (
                        "credits",
                        0.2,
                        "Credits to enhance your journey with powerful items.",
                    ),
                    ("gleam", 0.25, "A special gleam Pokemon abilities!"),
                    ("shiny", 0.15, "A Rare Shiny Pokemon"),
                    (
                        "mythic_chest",
                        0.1,
                        "A chest containing higher-tier items and legendary treasures!",
                    ),
                ],
                "image_url": "https://media.discordapp.net/attachments/1301161012656869438/1311618584291704883/75_Sem_Titulo_20241128060244.png?ex=6749837f&is=674831ff&hm=6939dea91583815ef9112dbf1adbe1793567e38289a8df17c64f766d9e955754&=&format=webp&quality=lossless&width=88&height=88",
            },
            "MYTHIC": {
                "rewards": [
                    (
                        "gems",
                        0.25,
                        "Gleaming gems to power your collection and purchases.",
                    ),
                    (
                        "credits",
                        0.2,
                        "Exclusive credits for premium in-game purchases.",
                    ),
                    ("boostedgleam", 0.1, "A High-tier Gleam Pokemon"),
                    ("boostedshiny", 0.08, "A High-tier Shiny Pokemon!"),
                    (
                        "shadowstreak",
                        0.18,
                        "Mysterious shadow energy to unlock powerful Pokemon.",
                    ),
                    (
                        "legend_chest",
                        0.05,
                        "A legendary chest containing treasures beyond imagination.",
                    ),
                ],
                "image_url": "https://media.discordapp.net/attachments/1301161012656869438/1311618583943708712/75_Sem_Titulo_20241128060156.png?ex=6749837f&is=674831ff&hm=1aa6351a3c11ff05796ddeeda398b2f0b06b2297ee657fbbf966bb04402c35b3&=&format=webp&quality=lossless&width=88&height=88",
                "description": "A mysterious chest with rare treasures. Only for the daring!",
                "emoji": "🌀",
                "color": discord.Color.blue(),
            },
            "LEGEND": {
                "rewards": [
                    ("gems", 0.17, "Gleaming gems for top-tier adventures!"),
                    (
                        "credits",
                        0.17,
                        "Credits to purchase the rarest and most powerful items.",
                    ),
                    (
                        "redeems",
                        0.1,
                        "The Premium In-game currency for redeeming anything.",
                    ),
                    ("boostedgleam", 0.22, "A rare but high-tier Pokemon."),
                    ("boostedshiny", 0.16, "A powerful shiny Pokemon."),
                    (
                        "voucher",
                        0.00002,
                        (
                            f"🎊 You received a Voucher!! 🎊\n"
                            "This means you can submit your own artwork for any unreleased Gleam Pokemon!\n"
                            "It will then be added to the following months lineup for everyone to obtain!\n"
                            "Message any staff in Mewbot's Official Server for more information!\n"
                        ),
                    ),
                    ("shadowstreak", 0.17, "Shadow energy with mysterious properties."),
                    (
                        "redeems",
                        0.00998,
                        "The ultimate currency for redeemable items, rewards and Pokemon!",
                    ),
                ],
                "image_url": "https://media.discordapp.net/attachments/1301161012656869438/1311618793562181642/75_Sem_Titulo_20241128060443.png?ex=674983b1&is=67483231&hm=d3b658a22f84801763510bcaeee9af11085cc1901eaa1dabd409548419d13292&=&format=webp&quality=lossless&width=88&height=88",
                "description": "A legendary chest containing treasures beyond imagination. Are you worthy?",
                "emoji": "🔥",
                "color": discord.Color.gold(),
            },
            "MYSTERY": {
                "rewards": [
                
                ("radiant", 0.15, "A special radiant Pokémon with a unique appearance."),
                ("shadowstreak", 0.40, "Grants 75 shadow streak to boost shadow Pokémon odds."),
                ("shadowstreak2", 0.10, "Grants 150 shadow streak to significantly improve shadow Pokémon odds."),
                ("shadow", 0.02, "An elusive shadow Pokémon."),
                ("gleam", 0.20, "A rare gleam Pokémon."),
                ("boostedgleam", 0.08, "A high-IV gleam Pokémon."),
                ("voucher", 0.005, "An exclusive voucher for rare rewards."),
                ("credits", 0.18, "Shop credits for purchases."),

                ]

            }
        }

    # async def log_chest(self, ctx):
    #     async with ctx.bot.db[0].acquire() as pconn:
    #         await pconn.execute(
    #             "INSERT INTO skylog (u_id, command, args, jump, time) VALUES ($1, $2, $3, $4, $5)",
    #             ctx.author.id,
    #             ctx.command.qualified_name,
    #             " ".join([str(x) for x in ctx.args]),
    #             ctx.jump_url,
    #             ctx.created_at.replace(tzinfo=None),
    #         )

    async def _maybe_spawn_event(self, ctx, chance):
        """
        Temporary method for spawning additional event pokemon.
        Spawns an event radiant for users who do not have one.

        Returns a string for user facing output.
        """
        if random.random() > chance:
            return ""
        if not self.EVENT_ACTIVE:
            return ""
        options = []
        async with ctx.bot.db[0].acquire() as pconn:
            for p in self.EVENT_ACTIVE:
                if not await pconn.fetchval(
                    "SELECT count(id) FROM pokes WHERE id in (select unnest(u.pokes) from users u where u.u_id = $1) AND radiant = true AND pokname = $2",
                    ctx.author.id,
                    p,
                ):
                    options.append(p)
        if not options:
            return ""
        poke = random.choice(options)
        await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, poke, skin="gleam")
        return self.EVENT_ACTIVE[poke]

    async def display_chest(self, ctx, chest: str):
        embed = discord.Embed(
            title="Opening Chest...",
            description="Explore the rewards you can get from each chest!\nLearn more about its rewards!",
            color=discord.Color.orange(),
        )

        rewards_message = ""
        for reward, weight, description in self.CHEST_DATA[chest.upper()]["rewards"]:
            rewards_message += f"• **{description}** (Chance: {weight * 100}%)\n"

        embed.add_field(
            name=f"{chest.upper() + ' CHEST'} Rewards:",
            value=rewards_message,
            inline=False,
        )

        # Add the chest image
        embed.set_thumbnail(url=self.CHEST_DATA[chest.upper()]["image_url"])

        # Send the embed to the channel
        return await ctx.send(embed=embed)

    async def open_chest(self, ctx, chest: str, chest_amount: int):
        chest_amount = max(1, chest_amount)
        opening_msg = await self.display_chest(ctx, chest)
        await asyncio.sleep(2)

        rewards, weights, descriptions = zip(*self.CHEST_DATA[chest.upper()]["rewards"])
        total = []

        for x in range(chest_amount):
            reward = random.choices(rewards, weights, k=1)[0]
            total.append(reward)
            gem_weight = (
                random.randint(1, 5)
                if chest == "common"
                else (
                    random.randint(5, 10)
                    if chest == "rare"
                    else (
                        random.randint(10, 15)
                        if chest == "mythic"
                        else (random.randint(20, 25) if chest == "legend" else 1)
                    )
                )
            )
            if reward.endswith("gleam"):
                pokemon = random.choice(self.CURRENTLY_ACTIVE)
                boosted = "boosted" in reward
                await ctx.bot.commondb.create_poke(
                    ctx.bot,
                    ctx.author.id,
                    pokemon,
                    skin="gleam",
                    boosted=boosted,
                )
                reward = "Boosted Gleam" if boosted else reward
            
            elif reward.endswith("radiant"):
                pokemon = random.choice(['Raging-bolt', 'Gouging-fire'])
                boosted = "boosted" in reward
                await ctx.bot.commondb.create_poke(
                    ctx.bot,
                    ctx.author.id,
                    pokemon,
                    skin="radiant",
                    boosted=boosted,
                )
                reward = "Boosted Radiant" if boosted else reward

            elif reward == "shadowstreak":
                amount = 75 if chest == "MYSTERY" else gem_weight * 5 
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE users SET chain = chain + $1 WHERE u_id = $2",
                        amount,
                        ctx.author.id,
                    )
                reward = "Shadow Streak"
            
            elif reward == "shadowstreak2":
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE users SET chain = chain + 150 WHERE u_id = $2",
                        amount,
                        ctx.author.id,
                    )
                reward = "Shadow Streak"

            elif reward.endswith("shiny"):
                pokemon = random.choice(totalList)
                boosted = "boosted" in reward
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon, shiny=True, boosted=boosted
                )
                reward = "Boosted Shiny" if boosted else reward
                
            elif reward.endswith("shadow"):
                async with ctx.bot.db[0].acquire() as pconn:
                    pokemon = await pconn.fetchval(
                        "UPDATE users SET chain = chain + 5000 WHERE u_id = $1 RETURNING hunt;",
                        ctx.author.id,
                    )
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, pokemon,
                )
                reward = "Shadow Pokemon"

            elif reward.endswith("chest"):

                await self.bot.commondb.add_bag_item(ctx.author.id, reward, 1, True)
                reward = f"{reward.split('_')[0]} Chest!"

            elif reward == "gems":
                await self.bot.commondb.add_bag_item(
                    ctx.author.id,
                    "radiant_gem",
                    gem_weight * (1 if random.choice([True, False]) else 2),
                    True,
                )

            elif reward == "redeems":
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                        gem_weight,
                        ctx.author.id,
                    )

            elif reward == "voucher":
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE account_bound SET vouchers = vouchers + 1 WHERE u_id = $1",
                        ctx.author.id,
                    )
                # Need to log this
                await ctx.bot.get_partial_messageable(1214302673093005323).send(
                    f"__**Voucher Summoned from Abyss**__\n\N{SMALL BLUE DIAMOND}-**{ctx.author.name}** - ``{ctx.author.id}`` has unlocked a voucher within **{ctx.guild.name}** - ``{ctx.guild.id}``\n"
                )
            # elif reward == "ev":
            #     amount = 250
            #     async with ctx.bot.db[0].acquire() as pconn:
            #         await pconn.execute(
            #             "UPDATE users SET evpoints = evpoints + $1 WHERE u_id = $2",
            #             amount,
            #             ctx.author.id,
            #         )
            #     msg = f"You received {amount} ev points!\n"

            elif reward == "credits":
                amount = ((gem_weight // 1.75) * 100000) // 1.5
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE users SET mewcoins = mewcoins + $1 WHERE u_id = $2",
                        amount,
                        ctx.author.id,
                    )

        for index, step in enumerate(range(0, chest_amount, 10)):
            description = ""
            for x in total[step : step + 10]:
                description += (
                    f"🎉 You received **{x.capitalize()}**!\n\n*{descriptions[rewards.index(x)]}*"
                    + "\n"
                )
            # Send result as an embed
            embed = discord.Embed(
                title=f"{ctx.bot.misc.get_emote(chest.upper() + '_CHEST')} {chest.capitalize()} Chest Opened!",
                description=description,
                color=random.choice(
                    (16711888, 0xFFB6C1, 0xFF69B4, 0xFFC0CB, 0xC71585, 0xDB7093)
                ),
            )
            embed.set_footer(text="Keep exploring and collecting chests!")
            (
                await opening_msg.edit(embed=embed)
                if index == 0
                else await ctx.send(embed=embed)
            )
            await asyncio.sleep(1)

    @commands.hybrid_group()
    async def open(self, ctx): ...

    @open.group()
    async def chest(self, ctx): ...

    @chest.command()
    async def patreon(self, ctx):
        """Open a patreon chest which contains only skins!. (Work in Progress)"""
        ...
        pokemon, skin = random.choice(self.bot.misc.OLD_SKINS)
        async with ctx.bot.db[0].acquire() as pconn:
            pats = await pconn.fetchval(
                "SELECT pat_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if not pats:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if pats <= 0:
                await ctx.send("You do not have any Pat Chests!")
                return
        await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, pokemon, skin=skin)

        await ctx.send(
            embed=make_embed(
                title=f"**Congratulations! You received a {skin} {pokemon}!**",
                icon_url="https://media.discordapp.net/attachments/1301161012656869438/1301421098495250462/62_Sem_Titulo_20241031024106.png?ex=673c2559&is=673ad3d9&hm=869989f2e98e9570e44c0bc859756a179ee0ba25b02b7686e872dc8ae65728ad&=&format=webp&quality=lossless&width=176&height=176",
            )
        )

        await self.bot.commondb.remove_bag_item(ctx.author.id, "pat_chest", 1, True)

    @chest.command()
    @discord.app_commands.describe(
        amount="Amount of Common chests.",
    )
    async def common(self, ctx, amount: int = 1):
        """Open a common chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            common_chest = await pconn.fetchval(
                "SELECT common_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if common_chest is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if common_chest < 1:
                await ctx.send("You do not have any Common Chests!")
                return
            await self.bot.commondb.remove_bag_item(
                ctx.author.id, "common_chest", 1 * amount, True
            )
        await self.open_chest(ctx, "common", amount)

    @chest.command()
    @discord.app_commands.describe(
        amount="Amount of rare chests.",
    )
    async def rare(self, ctx, amount: int = 1):
        """Open a rare chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            rare_chest = await pconn.fetchval(
                "SELECT rare_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if rare_chest is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if rare_chest < 1:
                await ctx.send("You do not have any Rare Chests!")
                return
        await self.bot.commondb.remove_bag_item(
            ctx.author.id, "rare_chest", 1 * amount, True
        )
        await self.open_chest(ctx, "rare", amount)

    @chest.command()
    @discord.app_commands.describe(
        amount="Amount of Mythic chests.",
    )
    async def mythic(self, ctx, amount: int = 1):
        """Open a mythic chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            mythic_chest = await pconn.fetchval(
                "SELECT mythic_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if mythic_chest is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if mythic_chest < 1:
                await ctx.send("You do not have any Mythic Chests!")
                return
        await self.bot.commondb.remove_bag_item(
            ctx.author.id, "mythic_chest", 1 * amount, True
        )
        await self.open_chest(ctx, "mythic", amount)

    @chest.command()
    @discord.app_commands.describe(
        amount="Amount of Legend chests.",
    )
    async def legend(self, ctx, amount: int = 1):
        """Open a legend chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            legend_chest = await pconn.fetchval(
                "SELECT legend_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
        if legend_chest is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            return
        if legend_chest < 1:
            await ctx.send("You do not have any Legend Chests!")
            return
        await self.bot.commondb.remove_bag_item(
            ctx.author.id, "legend_chest", 1 * amount, True
        )
        await self.open_chest(ctx, "legend", amount)

    @chest.command()
    async def exalted(self, ctx):
        async with ctx.bot.db[0].acquire() as pconn:
            exalted_chest = await pconn.fetchval(
                "SELECT exalted_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if exalted_chest is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if exalted_chest <= 0:
                await ctx.send("You do not have any Exalted Chests!")
                return
            await self.bot.commondb.remove_bag_item(
                ctx.author.id, "exalted_chest", 1, True
            )
            # Give Redeems
            amount = 200
            await pconn.execute(
                "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                amount,
                ctx.author.id,
            )
            msg = f"You've received 200 redeems!\n"
            # Give Gems
            gems = random.randint(10, 15)
            await self.bot.commondb.add_bag_item(
                ctx.author.id, "radiant_gem", gems, True
            )
            msg += f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!"
        await ctx.send(msg)

    @chest.command(name="art")
    async def art_team(self, ctx):
        """Open an art chest."""
        async with ctx.bot.db[0].acquire() as pconn:
            art_chest = await pconn.fetchval(
                "SELECT art_chest FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if art_chest is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            if art_chest <= 0:
                await ctx.send("You do not have any Art Chests!")
                return
        await self.bot.commondb.remove_bag_item(ctx.author.id, "art_chest", 1, True)

        options = list(self.CURRENTLY_ACTIVE)

        embed = make_embed(title="Which pokemon do you want?")

        selectView = ListSelectView(ctx, embed, options)

        choice = await selectView.wait()

        if not choice:
            await ctx.send("You did not select in time, cancelling.")
            return

        await ctx.bot.commondb.create_poke(
            ctx.bot,
            user_id=ctx.author.id,
            pokemon=choice,
            skin="gleam",
            boosted=True,
        )

        await selectView.message.edit(
            embed=make_embed(
                title=f"**Congratulations! You received a boosted gleam {choice}!**"
            )
        )

        return

        reward = random.choices(
            (
                "boostedshinylegendary",
                "redeem",
                "gleam",
                "boostedgleam",
                "boostedshiny",
            ),
            weights=(0.015, 0.10, 0.315, 0.245, 0.325),
        )[0]

        if reward == "custom":
            msg = "You have received a public voucher that allows you to submit your own recolor with background for any unreleased gleam pokemon, and it will be added to the following months lineup for everyone to obtain! Message Sky in the official server for more information!\nAlso, you of course get the one you design guaranteed. "
            await ctx.bot.get_partial_messageable(998291646443704320).send(
                f"<@631840748924436490> USER ID `{ctx.author.id}` HAS WON A 'Totally Custom Pokemon skin PUBLIC voucher'!"
            )
        elif reward == "boostedshinylegendary":
            pokemon = random.choice(LegendList)
            await ctx.bot.commondb.create_poke(
                ctx.bot,
                ctx.author.id,
                pokemon,
                boosted=True,
                shiny=True,
            )
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        elif reward == "boostedshiny":
            pokemon = random.choice(pList)
            await ctx.bot.commondb.create_poke(
                ctx.bot,
                ctx.author.id,
                pokemon,
                boosted=True,
                shiny=True,
            )
            msg = f"You received a shiny boosted IV {pokemon}!\n"
        elif reward == "redeem":
            amount = random.randint(30, 50)
            async with ctx.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE users SET redeems = redeems + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
            msg = f"You received {amount} redeems!\n"

        # elif reward == "radiant":
        # pokemon = random.choice(self.CURRENTLY_ACTIVE)
        # await ctx.bot.commondb.create_poke(
        # ctx.bot, ctx.author.id, pokemon, skin="radiant", tradable=False
        # )
        # msg = f"<a:quagwalk:998519974400380948> **Congratulations! You received a boosted radiant {pokemon}!**\n"

        elif reward == "gleam":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(
                ctx.bot, ctx.author.id, pokemon, skin="gleam", tradable=False
            )
            msg = f"<a:quagwalk:998519974400380948> **Congratulations! You received a gleam {pokemon}!**\n"

        elif reward == "boostedgleam":
            pokemon = random.choice(self.CURRENTLY_ACTIVE)
            await ctx.bot.commondb.create_poke(
                ctx.bot,
                ctx.author.id,
                pokemon,
                skin="gleam",
                boosted=True,
            )
            msg = f"<a:quagwalk:998519974400380948> **Congratulations! You received a boosted gleam {pokemon}!**\n"

        gems = random.randint(10, 15)
        await self.bot.commondb.add_bag_item(ctx.author.id, "radiant_gem", gems, True)
        msg += (
            f"You also received {gems} Gleam Gems <a:radiantgem:774866137472827432>!\n"
        )
        msg += await self._maybe_spawn_event(ctx, 0.33)
        await ctx.send(msg)

    @commands.hybrid_group()
    async def gleam(self, ctx): ...

    @gleam.command()
    async def packs(self, ctx):
        """Get Information of Gleam Packs"""
        desc = ""
        for idx, pack in enumerate(self.PACKS, start=1):
            desc += f"**{idx}.** __{pack[0]}__ - <a:radiantgem:774866137472827432>x{pack[1]}\n"
        desc += f"\nUse `/gleam` with the number you want to buy."
        e = discord.Embed(
            title="Gleam Gem Shop",
            description=desc,
            color=ctx.bot.get_random_color(),
        )
        await ctx.send(embed=e)

    @gleam.command()
    async def pack(
        self,
        ctx,
        pack: Literal[
            "1. Shiny Multiplier x1",
            "2. Battle Multiplier x1",
            "3. IV Multiplier x1",
            "4. Breeding Multiplier x1",
            "5. Legend Chest",
            "6. Gleam Pokemon (common & starter)",
            "7. Gleam Pokemon (legend & pseudo)",
        ],
    ):
        """Spend your gleam gems to obtain gleam Pokemon."""
        packnum = int(pack[0])
        if packnum < 1 or packnum > len(self.PACKS):
            await ctx.send("That is not a valid pack number.")
            return
        if ctx.author.id in self.purchaselock:
            await ctx.send("Please finish any pending purchases!")
            return
        self.purchaselock.append(ctx.author.id)

        if packnum == 5:
            amount = 1
            async with ctx.bot.db[0].acquire() as pconn:
                if not await pconn.fetchval(
                    "SELECT exists(SELECT * from users WHERE u_id = $1)", ctx.author.id
                ):
                    await ctx.send("You have not started!\nStart with `/start` first.")
                    self.purchaselock.remove(ctx.author.id)
                    return

                await pconn.execute(
                    "INSERT INTO gleampackstore VALUES ($1, 0, 0) ON CONFLICT DO NOTHING",
                    ctx.author.id,
                )
                info = await pconn.fetchrow(
                    "SELECT * FROM gleampackstore WHERE u_id = $1", ctx.author.id
                )

            if not info:
                info = {"u_id": ctx.author.id, "bought": 0, "restock": 0}
            else:
                info = {
                    "u_id": info["u_id"],
                    "bought": info["bought"],
                    "restock": int(info["restock"]),
                }

            max_packs = 300 if ctx.author.id == 634179052512739340 else 100
            restock_time = 604800

            if info["restock"] <= int(time.time() // restock_time):
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE gleampackstore SET bought = 0, restock = $1 WHERE u_id = $2",
                        str(int(time.time() // restock_time) + 1),
                        ctx.author.id,
                    )
                info = {
                    "u_id": ctx.author.id,
                    "bought": 0,
                    "restock": int(time.time() // restock_time) + 1,
                }

            if not amount:
                if info["restock"] != 0:
                    desc = f"You have bought {info['bought']} gleam pack 5 this week.\n"
                    if info["bought"] >= max_packs:
                        desc += "You cannot buy any more this week."
                    else:
                        desc += "Buy more !"
                    embed = discord.Embed(
                        title="Buy Gleam Pack 5",
                        description=desc,
                        color=0xFFB6C1,
                    )
                    embed.set_footer(
                        text="Gleam Pack 5 restocks every Wednesday at 8pm ET."
                    )
                else:
                    embed = discord.Embed(
                        title="Buy Gleam Pack 5",
                        description="You haven't bought any Gleam packs yet!!",
                        color=0xFFB6C1,
                    )

                await ctx.send(embed=embed)
                self.purchaselock.remove(ctx.author.id)
            else:
                if info["bought"] + amount > max_packs:
                    await ctx.send(
                        f"You can't buy more than {max_packs} per week!  You've already bought {info['bought']}."
                    )
                    self.purchaselock.remove(ctx.author.id)
                    return
        pack = self.PACKS[packnum - 1]

        if not await ConfirmView(
            ctx,
            f"Are you sure you want to buy {pack[0]} for <a:radiantgem:774866137472827432>x{pack[1]}?",
        ).wait():
            await ctx.send("Purchase cancelled.")
            self.purchaselock.remove(ctx.author.id)
            return

        choice = ""
        if packnum in (6, 7):
            if packnum == 6:
                options = list(self.COMMON)
            elif packnum == 7:
                options = list(self.LEGEND)
            if not options:
                await ctx.send(
                    "There are currently no valid pokemon in the pool. Please try again later."
                )
                self.purchaselock.remove(ctx.author.id)
                return
            choice = await ListSelectView(
                ctx, "Which pokemon do you want?", options
            ).wait()
            if choice is None:
                await ctx.send("You did not select in time, cancelling.")
                self.purchaselock.remove(ctx.author.id)
                return
        async with ctx.bot.db[0].acquire() as pconn:
            inventory = await pconn.fetchrow(
                "SELECT * FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            if inventory is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                self.purchaselock.remove(ctx.author.id)
                return
            inventory = dict(inventory)

            radiant_gems = inventory["radiant_gem"]
            if radiant_gems < pack[1]:
                await ctx.send("You cannot afford that pack!")
                self.purchaselock.remove(ctx.author.id)
                return
            await self.bot.commondb.remove_bag_item(
                ctx.author.id, "radiant_gem", pack[1], True
            )
            if packnum in (1, 2, 3, 4):
                if packnum == 1:
                    name = "shiny_multiplier"
                    item = inventory["shiny_multiplier"]
                elif packnum == 2:
                    name = "battle_multiplier"
                    item = inventory["battle_multiplier"]
                elif packnum == 3:
                    name = "iv_multiplier"
                    item = inventory["iv_multiplier"]
                elif packnum == 4:
                    name = "breeding_multiplier"
                    item = inventory["breeding_multiplier"]
                if item >= 50:
                    await ctx.send("You have hit the cap for that multiplier!")
                    self.purchaselock.remove(ctx.author.id)
                    return
                gain = min(item + 1, 50)
                # This isn't good but set values so it's okay...
                await pconn.execute(
                    f"UPDATE account_bound SET {name} = $1 WHERE u_id = $2",
                    gain,
                    ctx.author.id,
                )
            elif packnum == 5:
                await pconn.execute(
                    "UPDATE gleampackstore SET bought = bought + $1 WHERE u_id = $2",
                    amount,
                    ctx.author.id,
                )
                if info["restock"] == 0:
                    await pconn.execute(
                        "UPDATE gleampackstore SET restock = $1 WHERE u_id = $2",
                        str(int(time.time() // restock_time) + 1),
                        ctx.author.id,
                    )
                await self.bot.commondb.add_bag_item(
                    ctx.author.id, "legend_chest", 1, True
                )
            elif packnum in (6, 7):
                await ctx.bot.commondb.create_poke(
                    ctx.bot, ctx.author.id, choice, skin="gleam", boosted=True
                )
        self.purchaselock.remove(ctx.author.id)
        await ctx.send(
            f"You have successfully bought {pack[0]} for <a:radiantgem:774866137472827432>x{pack[1]}."
        )


async def setup(bot):
    await bot.add_cog(Chests(bot))
