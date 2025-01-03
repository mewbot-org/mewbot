import discord
import asyncio

from discord.ext import commands
from mewcogs.pokemon_list import *
from mewcogs.json_files import *
from mewutils.misc import (
    get_battle_emoji,
    get_trade_emoji,
    get_stone_emoji,
    get_form_emoji,
    pagify,
    SlashMenuView,
    MenuView,
)
from typing import Literal


# This is temporary until pagify under mewutils.misc can be updated to match below
# Requires bot restart, noted under todo.
def shop_pagify(
    text: str,
    *,
    per_page: int = 15,
    sep: str = "\n",
    base_embed=None,
    footer: str = None,
):
    """
    Splits the provided `text` into pages.

    The text is split by `sep`, then `per_page` are recombined into a "page".
    This does not validate page length restrictions.

    If `base_embed` is provided, it will be used as a template. The description
    field will be filled with the pages, and the footer will show the page number.
    Returns List[str], or List[discord.Embed] if `base_embed` is provided.
    """
    page = ""
    pages = []
    raw = text.strip().split(sep)
    total_pages = ((len(raw) - 1) // per_page) + 1
    for idx, part in enumerate(raw):
        page += part + sep
        if idx % per_page == per_page - 1 or idx == len(raw) - 1:
            # Strip out the last sep
            page = page[: -len(sep)]
            if base_embed is not None:
                embed = base_embed.copy()
                embed.description = page
                if footer is None:
                    embed.set_footer(text=f"Page {(idx // per_page) + 1}/{total_pages}")
                else:
                    embed.set_footer(
                        text=f"Page {(idx // per_page) + 1}/{total_pages} | {footer}"
                    )
                pages.append(embed)
            else:
                pages.append(page)
            page = ""
    return pages


class DropdownSelect(discord.ui.Select):
    def __init__(self, credits, ctx: commands.Context):
        options = [
            discord.SelectOption(
                label="Minigames",
                description="Rods & Shovels for Minigames",
                emoji=f"{ctx.bot.misc.get_emote('fishing_rod')}",
            ),
            discord.SelectOption(
                label="Items",
                description="Items for Pokemon, Breeding, etc",
                emoji=f"{ctx.bot.misc.get_emote('destiny_knot')}",
            ),
            discord.SelectOption(
                label="Battle Items",
                description="Items for Dueling Friends or NPCs",
                emoji=f"{ctx.bot.misc.get_emote('focus_sash')}",
            ),
            discord.SelectOption(
                label="Trade Items",
                description="Items Held by Pokemon when being Traded",
                emoji=f"{ctx.bot.misc.get_emote('kings_rock')}",
            ),
            discord.SelectOption(
                label="Mega & Evo Stones",
                description="Trigger Type or Mega Evolutions",
                emoji=f"{ctx.bot.misc.get_emote('mega_stone')}",
            ),
            discord.SelectOption(
                label="Plates, Memories & Masks",
                description="Change Arceus/Judgement, Silvally Typing and Ogerpon/Ivy cudgel Typing",
                emoji=f"{ctx.bot.misc.get_emote('draco_plate')}",
            ),
            discord.SelectOption(
                label="Forms",
                description="Items that trigger Form changes",
                emoji=f"{ctx.bot.misc.get_emote('reveal_glass')}",
            ),
            discord.SelectOption(
                label="Vitamins",
                description="Help with increasing EVs on Pokemon",
                emoji=f"{ctx.bot.misc.get_emote('hp_up')}",
            ),
            discord.SelectOption(
                label="Berry Seeds",
                description="Use to grow berries in your farm",
                emoji=f"{ctx.bot.misc.get_emote('iapapa_berry')}",
            ),
            discord.SelectOption(
                label="Monthly Alpha Rotation",
                description="Purchase Rare Alpha Pokemon",
                emoji=f"{ctx.bot.misc.get_emote('alpha_poke')}",
            ),
        ]
        self.credits = credits
        self.ctx = ctx
        super().__init__(
            placeholder="Make your selection...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = interaction.data["values"][0]
        if self.view.choice == "Minigames":
            embed = discord.Embed(
                title="Minigame Equipment",
                description="Items give benefits through their respective activity!\n",
            )
            embed.add_field(
                name=f"Fishing Rods {interaction.client.misc.get_emote('fishing_rod')}",
                value=(
                    f"\n`Old Rod`: 5,000 credits"
                    f"\n`New Rod`: 10,000 credits"
                    f"\n`Good Rod`: 15,000 credits"
                    f"\n`Super Rod`: 20,000 credits"
                    f"\n`Ultra Rod`: 40,000 credits"
                ),
            )
            embed.add_field(
                name=f"Mining Shovels {interaction.client.misc.get_emote('shovel')}",
                value=(
                    f"\n`Old Shovel`: 5,000 credits"
                    f"\n`New Shovel`: 10,000 credits"
                    f"\n`Good Shovel`: 15,000 credits"
                    f"\n`Super Shovel`: 20,000 credits"
                    f"\n`Ultra Shovel`: 40,000 credits"
                ),
            )
            embed.set_footer(text=f"{interaction.user.name}'s bal: {self.credits:,}")
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == "Items":
            embed = discord.Embed(
                title="General Items",
                description="Various items that help with different parts of the bot.",
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('rare_candy')} Rare Candies",
                value="Increase Lvl by 1\n`/buy item rare candy`\nCost: 100 credits each",
                inline=True,
            )
            embed.add_field(
                name="🍫 Energy Refill",
                value="Refills your Energy!\n`/buy energy`\nCost: 25,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('everstone')} Everstone",
                value="Automatically stops evolutions\n`/buy item everstone`\nCost: 3,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('xp_block')} Exp Blocker",
                value="Stop any Exp Gain!\n`/buy item xp block`\nCost: 3,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('lucky_egg')} Lucky Egg",
                value="150% EXP Gain for selected Pokemon\n`/buy item lucky egg`\nCost: 5,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('soothe_bell')} Soothe Bell",
                value="50% Friendship Gain for selected Pokemon\n`/buy item soothe bell`\nCost: 5,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('ability_capsule')} Ability Capsule",
                value="Change selected Pokemon's Ability\n`/buy item ability capsule`\nCost: 10,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('poke_egg')} Daycare Space",
                value="Increases Daycare Spaces so you can breed more\n`/buy daycare`\nCost: 10,000 credits",
                inline=True,
            )
            embed.add_field(
                name="🛒 Market Space",
                value="Increases Market Spaces so you can list more Pokemon!\n`/buy item market space`\nCost: 30,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('destiny_knot')} Destiny Knot",
                value="Pass down 2-3 random IVs to an Offspring during Breeding\n`/buy item destiny knot`\nCost: 15,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('destiny_knot')} Ultra Destiny Knot",
                value="Pass down 2-5 random IVs to an Offspring during Breeding\n`/buy item ultra destiny knot`\nCost: 30,000 credits",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('evs')} EV Reset",
                value="Reset EVs on your selected Pokemon.\n`buy item ev reset`\nCost: 10,000 credits",
                inline=True,
            )
            embed.set_footer(text=f"{interaction.user.name}'s bal: {self.credits:,}")
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == "Battle Items":
            BATTLE_ITEMS = (
                await interaction.client.db[1].battle_items.find({}).to_list(None)
            )
            items = [t["item"] for t in BATTLE_ITEMS]
            prices = [t["price"] for t in BATTLE_ITEMS]
            desc = ""
            count = 1
            for idx, item in enumerate(items):
                emoji = interaction.client.misc.get_emote(item.lower())
                # So on each of these items essentially page break
                if count in [7, 14, 21, 28, 35, 42, 49, 56, 63, 70]:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`/buy item {item.lower().replace('_', ' ')}`\n\n"
                else:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`/buy item {item.lower().replace('_', ' ')}`\n"
                count += 1

            footer_text = "Each item cost 10,000 credits"
            embed = discord.Embed(title="Items for Battles!", color=3553600)
            pages = shop_pagify(desc, base_embed=embed, footer=footer_text)
            await SlashMenuView(interaction, pages).start()

        if self.view.choice == "Trade Items":
            TRADE_ITEMS = (
                await interaction.client.db[1].trade_items.find({}).to_list(None)
            )
            items = [t["item"] for t in TRADE_ITEMS]
            prices = [t["price"] for t in TRADE_ITEMS]
            desc = ""
            count = 1
            for idx, item in enumerate(items):
                price = prices[idx]
                emoji = interaction.client.misc.get_emote(item.lower())
                # So on each of these items essentially page break
                if count in [7, 14, 21]:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`/buy item {item.lower().replace('_', ' ')}`\n\n"
                else:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`/buy item {item.lower().replace('_', ' ')}`\n"
                count += 1

            footer_text = "Each item is 3,000 credits"
            embed = discord.Embed(title="Held Items for Trades!", color=3553600)
            pages = shop_pagify(desc, base_embed=embed, footer=footer_text)
            await SlashMenuView(interaction, pages).start()

        if self.view.choice == "Mega & Evo Stones":
            stones = [
                "sun",
                "dusk",
                "thunder",
                "fire",
                "ice",
                "water",
                "dawn",
                "leaf",
                "moon",
                "shiny",
            ]
            megastone = ["mega_stone_x", "mega_stone_y", "mega_stone"]
            desc = ""
            count = 1
            for stone in megastone:
                emoji = interaction.client.misc.get_emote(stone)
                desc += f"**{emoji} {stone.title().replace('_', ' ')}**\n`/buy item {stone.lower().replace('_', ' ')}`\n"
                count += 1

            for stone in stones:
                full_name = f"{stone}_stone"
                emoji = interaction.client.misc.get_emote(full_name)
                # So on each of these items essentially page break
                if count in [7, 14, 21, 28]:
                    desc += f"**{emoji} {full_name.title().replace('_', ' ')}**\n`/buy item {full_name.lower().replace('_', ' ')}`\n\n"
                else:
                    desc += f"**{emoji} {full_name.title().replace('_', ' ')}**\n`/buy item {full_name.lower().replace('_', ' ')}`\n"
                count += 1

            footer_text = "Each item is 3,000 credits"
            embed = discord.Embed(title="Evolution Stones!", color=3553600)
            pages = shop_pagify(desc, base_embed=embed, footer=footer_text)
            await SlashMenuView(interaction, pages).start()

        if self.view.choice == "Plates, Memories & Masks":
            embed = discord.Embed(
                title=f"Arceus Plates, Silvally Memories & Ogerpons' Masks",
                description=f"Plates are used for Arceus, they affect Arceus and Judgement's Type!\nMemories are used for Silvally, they affect Silvallys' Type\nMasks are used for Ogerpon, they affect its' type and the type of Ivy Cudgel\nCost 10,000 each - Buy with `/buy item draco plate`",
                color=0x0084FD,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Draco Plate**"
                    f"\n**Dread Plate**"
                    f"\n**Earth Plate**"
                    f"\n**Fist Plate**"
                    f"\n*Flame Plate**"
                    f"\n**Icicle Plate**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Splash Plate**"
                    f"\n**Sky Plate**"
                    f"\n**Pixie Plate**"
                    f"\n**Mind Plate**"
                    f"\n**Meadow Plate**"
                    f"\n**Insect Plate**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Spooky Plate**"
                    f"\n**Stone Plate**"
                    f"\n**Toxic Plate**"
                    f"\n**Zap Plate**"
                    f"\n**Iron Plate**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Dragon Memory**"
                    f"\n**Dark Memory**"
                    f"\n**Ground Memory**"
                    f"\n**Fighting Memory**"
                    f"\n**Fire Memory**"
                    f"\n**Ice Memory**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Steel Memory**"
                    f"\n<**Water Memory**"
                    f"\n**Fairy Memory**"
                    f"\n**Psychic Memory**"
                    f"\n**Grass Memory**"
                    f"\n**Bug Memory**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Ghost Memory**"
                    f"\n**Rock Memory**"
                    f"\n<**Poison Memory**"
                    f"\n**Electric Memory**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"\n**Wellspring Mask**"
                    f"\n**Hearthflame Mask**"
                    f"\n**Cornerstone Mask**"
                ),
                inline=True,
            )
            embed.set_footer(text=f"{interaction.user.name}'s bal: {self.credits:,}")
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == "Forms":
            FORM_ITEMS = (
                await interaction.client.db[1].form_items.find({}).to_list(None)
            )
            items = [t["item"] for t in FORM_ITEMS]
            prices = [t["price"] for t in FORM_ITEMS]
            descriptions = [t["description"] for t in FORM_ITEMS]
            desc = ""
            count = 1
            for idx, item in enumerate(items):
                price = prices[idx]
                description = descriptions[idx]
                emoji = interaction.client.misc.get_emote(item.lower())
                # So on each of these items essentially page break
                if count in [5, 10, 15, 20, 25, 30, 35]:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n{description}\n`/buy item {item.title().replace('_', ' ')}` - {price:,.0f} credits\n\n"
                else:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n{description}\n`/buy item {item.title().replace('_', ' ')}` - {price:,.0f} credits\n"
                count += 1

            embed = discord.Embed(title="Form Items!", color=3553600)
            pages = pagify(desc, base_embed=embed)
            await SlashMenuView(interaction, pages).start()

        if self.view.choice == "Vitamins":
            embed = discord.Embed(
                title="Pokemon Vitamins!",
                description="Each vitamin increases a different Effort Value!\nEVs are a boost to a particular stat. All costing 100 credits each!",
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('hp_up')} HP Up",
                value="Increases HP EV\n`/buy vitamin hp-up`",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('protein')} Protein",
                value="Increases Attack EV\n`/buy vitamin protein`",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('iron')} Iron",
                value="Increases Defense EV\n`/buy vitamin iron`",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('calcium')} Calcium",
                value="Increases Special Attack EV\n`/buy vitamin calcium`",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('zinc')} Zinc",
                value="Increases Special Defense EV\n`/buy vitamin zinc`",
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('carbos')} Carbos",
                value="Increases Speed EV\n`/buy vitamin carbos`",
                inline=True,
            )
            embed.set_footer(text=f"{interaction.user.name}'s bal: {self.credits:,}")
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == "Berry Seeds":
            embed = discord.Embed(
                title="Berry Seeds",
                description="Used for Farming, plant to gain a berry!\nBuy with `/buy item [seed name]`, they all cost 2,500 credits.",
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"{interaction.client.misc.get_emote('aguav_berry')} **Aguav Seed**\n"
                    f"{interaction.client.misc.get_emote('apicot_berry')} **Apicot Seed**\n"
                    f"{interaction.client.misc.get_emote('aspear_berry')} **Aspear Seed**\n"
                    f"{interaction.client.misc.get_emote('cheri_berry')} **Cheri Seed**\n"
                    f"{interaction.client.misc.get_emote('chesto_berry')} **Chesto Seed**\n"
                    f"{interaction.client.misc.get_emote('figy_berry')} **Figy Seed**\n"
                    f"{interaction.client.misc.get_emote('ganlon_berry')} **Ganlon Seed**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"{interaction.client.misc.get_emote('iapapa_berry')} **Iapapa Seed**\n"
                    f"{interaction.client.misc.get_emote('lansat_berry')} **Lansat Seed**\n"
                    f"{interaction.client.misc.get_emote('liechi_berry')} **Liechi Seed**\n"
                    f"{interaction.client.misc.get_emote('lum_berry')} **Lum Seed**\n"
                    f"{interaction.client.misc.get_emote('mago_berry')} **Mago Seed**\n"
                    f"{interaction.client.misc.get_emote('micle_berry')} **Micle Seed**\n"
                    f"{interaction.client.misc.get_emote('pecha_berry')} **Pecha Seed**"
                ),
                inline=True,
            )
            embed.add_field(
                name=f"{interaction.client.misc.get_emote('blank')}",
                value=(
                    f"{interaction.client.misc.get_emote('persim_berry')} **Persim Seed**\n"
                    f"{interaction.client.misc.get_emote('petaya_berry')} **Petaya Seed**\n"
                    f"{interaction.client.misc.get_emote('rawst_berry')} **Rawst Seed**\n"
                    f"{interaction.client.misc.get_emote('salac_berry')} **Salac Seed**\n"
                    f"{interaction.client.misc.get_emote('sitrus_berry')} **Sitrus Seed**\n"
                    f"{interaction.client.misc.get_emote('starf_berry')} **Starf Seed**\n"
                    f"{interaction.client.misc.get_emote('wiki_berry')} **Wiki Seed**\n"
                ),
                inline=True,
            )
            embed.set_footer(text=f"{interaction.user.name}'s bal: {self.credits:,}")
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == "Monthly Alpha Rotation":
            embed = discord.Embed(
                title="Monthly Alpha Rotation",
                description="Purchase a new breed of Rare Pokemon called Alpha Pokemon, these come with preconfigured moves!\nYou can get one with `/redeem alpha`, they all cost 850,500 credits.",
            )

            for alpha_pokemon in self.ctx.bot.commondb.ALPHA_POKEMON:
                embed.add_field(
                    name=f"{interaction.client.misc.get_emote('blank')}",
                    value=(
                        f"{self.ctx.bot.misc.get_random_egg_emote()} **"
                        + alpha_pokemon
                        + "**"
                    ),
                    inline=True,
                )
            embed.set_footer(text=f"{interaction.user.name}'s bal: {self.credits:,}")
            await interaction.response.edit_message(embed=embed)


class ShopView(discord.ui.View):
    """View that helps character commands"""

    def __init__(self, ctx, credits):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.event = asyncio.Event()
        self.message = ""
        self.add_item(DropdownSelect(credits, ctx))

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
        self.stop()

    async def on_error(self, error, item, interaction):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def wait(self):
        """Returns the user's choice, or None if they did not choose in time."""
        # Start creating base embed
        embed = discord.Embed(
            title=f"Mewbot Shop",
            description=f"Choose an option from the dropdown menu below!",
            color=0x4F2683,
        )
        embed.set_image(url="https://mewbot.xyz/shop_image.png")
        self.message = await self.ctx.send(embed=embed, view=self)
        await self.event.wait()


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def shop(self, ctx):
        """
        Shop command
        """
        pass

    @shop.command()
    async def view(self, ctx):
        """New Shop with Menu"""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("Sorry, this isn't ready yet!")
        # return
        async with ctx.bot.db[0].acquire() as pconn:
            credits = await pconn.fetchval(
                "SELECT mewcoins FROM users WHERE u_id = $1", ctx.author.id
            )
        await ShopView(ctx, credits).wait()

    @shop.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @discord.app_commands.describe(
        section="What section of the shop do you want to look at?"
    )
    async def old(
        self,
        ctx,
        section: Literal[
            "forms",
            "mega stones",
            "items",
            "trade items",
            "battle items",
            "evolution stones",
            "arceus plates",
            "vitamins",
            "rods",
        ],
    ):
        """Old shop system"""
        if not section:
            e = discord.Embed(
                title="Shop Sections - containing Items you can buy in the Shop!",
                description=f"`/shop <section>`",
                color=3553600,
            )
            e.add_field(name="Forms", value=f"`/shop forms`", inline=False)
            e.add_field(name="Mega Pokemon", value=f"`/shop mega`", inline=False)
            e.add_field(name="Items", value=f"`/shop items`", inline=False)
            e.add_field(name="Trade items", value=f"`/shop trade items`", inline=False)
            e.add_field(
                name="Battle Items",
                value=f"`/shop battle items`",
                inline=False,
            )
            e.add_field(
                name="Stones",
                value=f"`/shop stones` Evolution stones",
                inline=False,
            )
            e.add_field(name="Vitamins", value=f"`/shop vitamins`", inline=False)
            e.add_field(name="Rods", value=f"`/shop rods`", inline=False)
            e.set_footer(
                text="Items can also be gotten through Item Drops from spawned Pokemon!"
            )
            await ctx.send(embed=e)
            return
        elif section == "rods":
            rods = [t["item"] for t in SHOP if "_rod" in t["item"]]
            prices = [t["price"] for t in SHOP if t["item"] in rods]
            e = discord.Embed(
                title="Fishing Rods!",
                description=f"Say `/buy item <rod_name>` to buy a Rod",
                color=3553600,
            )
            for idx, rod in enumerate(rods):
                e.add_field(
                    name=rod.capitalize().replace("-", " "),
                    value=f"Costs {prices[idx]} {ctx.bot.misc.emotes['CREDITS']}",
                )
            e.set_footer(
                text="Items can also be gotten through Item Drops from spawned Pokemon!"
            )
            await ctx.send(embed=e)
        elif section == "items":
            e = discord.Embed(
                title="Items to evolve or Boost stats, e.t.c", color=3553600
            )

            e.add_field(
                name="Rare Candies",
                value=f"Buy rare candies with `/buy candy <amount>`. Costs 100{ctx.bot.misc.emotes['CREDITS']} each!",
            )
            e.add_field(
                name="Energy Refill",
                value=f"Don't want to wait for your energy to be replenished? Buy energy refills with `/buy energy`. Costs 25000{ctx.bot.misc.emotes['CREDITS']}!",
            )
            e.add_field(
                name="Everstone",
                value=f"Buy the Everstone to automatically stop evolution! Costs 3,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="XP-Block",
                value=f"Stop any Pokemon from gaining Experience with the XP-Block. Costs 3,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Lucky Egg",
                value=f"Boost EXP Gain of your selected Pokemon by 150% Costs 5,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Soothe bell",
                value=f"Boost Friendship Gain of your Selected Pokemon by 50% Costs 5,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Ability Capsule",
                value=f"Change your Pokemons ability by buying the Ability Capsule! Costs 10,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Daycare Space",
                value=f"Buy an Extra Space in the Daycare to breed more Pokemon! Costs 10,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Market Space",
                value=f"Buy an extra space in the market to sell more pokemon! Costs 30,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Destiny Knot",
                value=f"Pass down 2-3 Random Stats to an Offspring during Breeding! Costs 15,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Ultra Destiny Knot",
                value=f"Pass down 2-5 Random Stats to an Offspring during Breeding! Costs 30,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="EV Reset",
                value=f"Reset EVs of your selected Pokemon with the EV reset! Costs 10,000{ctx.bot.misc.emotes['CREDITS']}",
            )
            e.add_field(
                name="Coin Case",
                value=f"Get a Coin Case and Enjoy MewBot's game corner! Costs 1000{ctx.bot.misc.emotes['CREDITS']}",
            )
            await ctx.send(embed=e)
        elif section == "evolution stones":
            e = discord.Embed(title="Evolution Stones", color=3553600)
            e.description = f"All Stones Cost 1,000{ctx.bot.misc.emotes['CREDITS']}!"
            e.description += "\nSun stone"
            e.description += "\nDusk stone"
            e.description += "\nThunder stone"
            e.description += "\nFire stone"
            e.description += "\nIce stone"
            e.description += "\nWater stone"
            e.description += "\nDawn stone"
            e.description += "\nLeaf stone"
            e.description += "\nMoon stone"
            e.description += "\nShiny stone"
            # e.add_field(name="Evo Stone", value="Evolves any Pokemon | Costs 10,000 Credits")
            await ctx.send(embed=e)

        elif section == "berry seeds":
            e = discord.Embed(title="Berry Seeds", color=3553600)
            e.description = f"All Seeds Cost 2,500{ctx.bot.misc.emotes['CREDITS']}!"
            e.description += "\nGanlon Seed"
            e.description += "\nApicot Seed"
            e.description += "\nLiechi Seed"
            e.description += "\nMicle Seed"
            e.description += "\nPetaya Seed"
            e.description += "\nSalac Seed"
            e.description += "\nStarf Seed"
            e.description += "\nAspear Seed"
            e.description += "\nCheri Seed"
            e.description += "\nChesto Seed"
            e.description += "\nLum Seed"
            e.description += "\nPecha Seed"
            e.description += "\nPersim Seed"
            e.description += "\nRawst Seed"
            e.description += "\nAguav Seed"
            e.description += "\nFigy Seed"
            e.description += "\nIapapa Seed"
            e.description += "\nMago Seed"
            e.description += "\nLansat Seed"
            # e.add_field(name="Evo Stone", value="Evolves any Pokemon | Costs 10,000 Credits")
            await ctx.send(embed=e)

        elif section == "forms":
            e = discord.Embed(
                title="Buy Items to change your pokemon Forms!!", color=3553600
            )
            e.add_field(
                name="Blue orb",
                value="Buy the Blue Orb to make your Kyogre Primal! | 10,000ℳ",
            )
            e.add_field(
                name="Red orb",
                value="Buy the Red Orb to make your Groudon Primal! | 10,000ℳ",
            )
            e.add_field(
                name="Meteorite",
                value="Have your Deoxys Interact with it to Get the Forms! | 10,500ℳ",
            )
            e.add_field(
                name="N-Solarizer",
                value="Buy the N-Solarizer to Fuse your Necrozma and a Solgaleo to Get Necrozma Dusk Forme! | 9,500ℳ",
            )
            e.add_field(
                name="N-Lunarizer",
                value="Buy the N-Lunarizer to Fuse your Necrozma and a Lunala to get Necrozma Dawn Forme! | 9,500ℳ",
            )
            e.add_field(
                name="Arceus Plates",
                value=f"Need Arceus Plates to Transform it?, just say `/shop plates`",
            )
            e.add_field(
                name="Light Stone",
                value="Buy this to Fuse your Kyurem with Reshiram for Kyurem-white! | 9,500ℳ",
            )
            e.add_field(
                name="Dark Stone",
                value="Buy this to Fuse your Kyurem with Zekrom for Kyurem-black | 9,500ℳ",
            )
            e.add_field(
                name="Reveal Glass",
                value="Buy this to Change the forms of the forces of nature! | 10,500ℳ",
            )
            e.add_field(
                name="Zygarde cell",
                value="Get Zygarde-complete by Buying the Zygarde Cell! | 15,000 ℳ",
            )
            e.add_field(
                name="Gracidea flower",
                value="Buy the Gracidea flower to Evolve your Shaymin to Shaymin-sky! | 7,500ℳ",
            )
            e.add_field(
                name="Griseous Orb",
                value="Buy the Griseous orb to evolve Giratina to it's Origin Forme! | 10,000ℳ",
            )
            e.add_field(
                name="Prison Bottle",
                value="Buy the Prison Bottle to evolve Hoopa into Unbound Forme! | 9,500ℳ",
            )
            await ctx.send(embed=e)
        elif section == "arceus plates":
            plates = {
                "Draco": "dragon",
                "Earth": "ground",
                "Dread": "dark",
                "Fist": "fighting",
                "Flame": "fire",
                "Icicle": "ice",
                "Insect": "bug",
                "Iron": "steel",
                "Meadow": "grass",
                "Mind": "psychic",
                "Pixie": "fairy",
                "Sky": "flying",
                "Splash": "water",
                "Spooky": "ghost",
                "Stone": "rock",
                "Toxic": "poison",
                "Zap": "electric",
            }
            e = discord.Embed(
                title="Arceus Plates!",
                description="All Plates Cost 10,000",
                color=3553600,
            )
            for plate in plates:
                type_ = plates.get(plate)
                e.add_field(
                    name=f"{plate} Plate",
                    value=f"Change Arceus and Judgement to {type_} type",
                )
            e.set_footer(
                text="Buy plates to evolve your Arceus!\nItems can also be gotten through Item Drops from spawned Pokemon!"
            )
            await ctx.send(embed=e)
        elif section == "mega stones":
            e = discord.Embed(
                title="Mega Stones!",
                description=f"Say `/buy <mega_stone>` to buy it",
                color=3553600,
            )
            e.add_field(
                name="Buy Mega Stones", value="To evolve your Pokemon to It's Mega Form"
            )
            e.add_field(
                name=f"Choose Between\nMega Stone - 2000{ctx.bot.misc.emotes['CREDITS']} \nMega stone X - 3500{ctx.bot.misc.emotes['CREDITS']}\nMega stone Y - 3500{ctx.bot.misc.emotes['CREDITS']}",
                value="To Mega your selected Pokemon",
            )
            await ctx.send(embed=e)
        elif section == "trade items":
            e = discord.Embed(title="Trade Item Shop!", color=3553600)
            e.description = (
                f"All Trade Items Cost 3,000 {ctx.bot.misc.emotes['CREDITS']}"
            )
            e.description += "\nDeep Sea Scale"
            e.description += "\n Sea Tooth"
            e.description += "\nDragon Scale"
            e.description += "\nElectirizer"
            e.description += "\nMagmarizer"
            e.description += "\nUp-grade"
            e.description += "\nKings Rock"
            e.description += "\nMetal Coat"
            e.description += "\nProtector"
            e.description += "\nPrism Scale"
            e.description += "\nRazor Fang"
            e.description += "\nRazor Claw"
            e.description += "\nOval Stone"
            e.description += "\nSachet"
            e.description += "\nWhipped Dream"
            e.description += "\nReaper cloth"
            e.description += "\nDubious disc"
            await ctx.send(embed=e)
        elif section == "vitamins":
            e = discord.Embed(
                title="Buy Vitamins!!",
                description=f"All Vitamins Cost 100{ctx.bot.misc.emotes['CREDITS']}!",
                color=3553600,
            )
            e.add_field(
                name="hp-up",
                value=f"`/buy vitamin hp-up` to boost your HP EV!",
            )
            e.add_field(
                name="Protein",
                value=f"`/buy vitamin protein` to boost your Attack EV!",
            )
            e.add_field(
                name="Iron",
                value=f"`/buy vitamin iron` to boost your Defense EV!",
            )
            e.add_field(
                name="Calcium",
                value=f"`/buy vitamin calcium` to boost your Special Attack EV!",
            )
            e.add_field(
                name="Zinc",
                value=f"`/buy vitamin zinc` to boost your Special Defense EV!",
            )
            e.add_field(
                name="Carbos",
                value=f"`/buy vitamin carbos` to boost your Speed EV!",
            )
            await ctx.send(embed=e)

        elif section == "battle items":
            items = [t["item"] for t in BATTLE_ITEMS]
            prices = [t["price"] for t in BATTLE_ITEMS]
            desc = ""
            for idx, item in enumerate(items):
                price = prices[idx]
                desc += f"**{item.capitalize().replace('-', ' ')}** - {price:,.0f}\n"

            embed = discord.Embed(
                title="Items for Battles! Buy with /buy <item>", color=3553600
            )
            pages = pagify(desc, base_embed=embed)
            await MenuView(ctx, pages).start()
        else:
            await ctx.send(
                "That is not a valid shop! To view the available shops, run `/shop`."
            )


async def setup(bot):
    await bot.add_cog(Shop(bot))
