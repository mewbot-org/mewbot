import discord
import time
import asyncio

from discord.ext import commands
from typing import Literal
from mewcogs.market import (
    PATREON_SLOT_BONUS,
    YELLOW_PATREON_SLOT_BONUS,
    SILVER_PATREON_SLOT_BONUS,
    CRYSTAL_PATREON_SLOT_BONUS,
)
from mewutils.misc import (
    get_pokemon_image, 
    get_badge_emoji,
    badge_pagify,
    ConfirmView,
    SlashMenuView
)

IMAGE_URLS = {
    "xmas/Maleskier": "https://lforebodingl.github.io/Kohaku-Images/trainers/skier_trainer_male.png",
    "xmas/Femaleskier": "https://lforebodingl.github.io/Kohaku-Images/trainers/skier_trainer_female.png",
    "xmas/Pyrce": "https://lforebodingl.github.io/Kohaku-Images/trainers/pyrce_trainer.png",
    "staff/Artsquad": "https://lforebodingl.github.io/Kohaku-Images/trainers/art_squad.png",
    "halloween/Hexmaniac": "https://lforebodingl.github.io/Kohaku-Images/trainers/hex_maniac_6.png",
    "summer/Phoebe": "https://lforebodingl.github.io/Kohaku-Images/trainers/phoebe.png",
    "summer/Brycen": "https://lforebodingl.github.io/Kohaku-Images/trainers/brycen.png",
    "halloween/Allister": "https://lforebodingl.github.io/Kohaku-Images/trainers/allister.png",
    "user/Youngster": "https://archives.bulbagarden.net/media/upload/4/48/Spr_DP_Youngster.png",
    "breeder/Breeder1": "https://lforebodingl.github.io/Kohaku-Images/trainers/breeder1.png",
    "breeder/Breeder2": "https://lforebodingl.github.io/Kohaku-Images/trainers/breeder2.png",
    "summer/Swimmerf": "https://lforebodingl.github.io/Kohaku-Images/trainers/swimmerf.png",
    "summer/Swimmerm": "https://lforebodingl.github.io/Kohaku-Images/trainers/swimmerm.png",
    "summer/Cyclist": "https://lforebodingl.github.io/Kohaku-Images/trainers/cyclist.png",
    "summer/Dancer": "https://lforebodingl.github.io/Kohaku-Images/trainers/dancer.png",
    "dev/Ghetsis": "https://lforebodingl.github.io/Kohaku-Images/trainers/ghetsis.png"
}

REGIONS = [
    "kanto", 
    "johto", 
    "hoenn", 
    "sinnoh", 
    "unova", 
    "kalos", 
    "alola", 
    "galar", 
    "paldea",
    "hisui"
]

def calculate_breeding_multiplier(level):
    difference = 0.02
    return f"{round((1 + (level) * difference), 2)}x"

def calculate_iv_multiplier(level):
    difference = 0.5
    return f"{round((level * difference), 1)}%"

    # This is commented out but here for future proofing. Dropdown select.
    # TODO: Update to match current profile layout and buttons
    # class DropdownSelect(discord.ui.Select):
    def __init__(self, bound_data, bag_data, player_data):
        options = [
            # discord.SelectOption(label="General", description="General Profile Page", emoji='🪪'),
            discord.SelectOption(
                label="Chests", description="Check your chest inventory", emoji="🎁"
            ),
            discord.SelectOption(
                label="Account Bound",
                description="Items tied to your Discord account",
                emoji="🔑",
            ),
        ]
        self.bound_data = bound_data
        self.bag_data = bag_data
        self.player_data = player_data

        super().__init__(
            placeholder="Make your selection...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = interaction.data["values"][0]
        if self.view.choice == "General":
            pokes = self.player_data["pokes"]
            tnick = self.player_data["tnick"]
            count = len(pokes)
            region = self.player_data["region"]
            is_staff = self.player_data["staff"]
            credits = self.player_data["mewcoins"]
            redeems = self.player_data["redeems"]
            gleam_gems = self.bound_data["radiant_gem"]
            if is_staff.lower() != "user":
                staff_msg = f"\nMewbot Staff Member: **{is_staff.capitalize()}**"

            embed = discord.Embed(
                title=f"{interaction.user.name}'s Profile!",
                description=f"Trainer Nick: **{tnick}**{staff_msg}",
            )
            embed.add_field(
                name="General Info",
                value=(
                    f"`Pokemon Caught`: {count:,}\n"
                    f"`Active Region`: {region.title()}"
                ),
                inline=True,
            )
            embed.add_field(
                name="Balances",
                value=(
                    f"`Credits`: {credits:,}\n"
                    f"`Redeems`: {redeems:,}\n"
                    f"`Gleam Gems`: {gleam_gems:,}"
                ),
                inline=True,
            )
            embed.set_thumbnail(
                url="https://archives.bulbagarden.net/media/upload/3/3a/Spr_B2W2_Ace_Trainer_M.png"
            )
            embed.set_footer(text=f"{interaction.user.name}'s Profile")
            try:
                await interaction.response.send_message(embed=embed)
            except:
                await interaction.followup.send(embed=embed)

        if self.view.choice == "Chests":
            async with interaction.client.db[0].acquire() as pconn:
                info = await pconn.fetchrow(
                    "SELECT rare, mythic, legend FROM cheststore WHERE u_id = $1",
                    interaction.user.id,
                )
            disabled = self.player_data["visible"]
            # running chest totals
            common = self.bound_data["common_chest"]
            rare = self.bound_data["rare_chest"]
            mythic = self.bound_data["mythic_chest"]
            legend = self.bound_data["legend_chest"]
            exalted = self.bound_data["exalted_chest"]
            embed = discord.Embed(
                title=f"{interaction.user}'s Chests",
                color=0xFFB6C1,
            )
            embed.add_field(
                name="Common",
                value=f"<:cchest1:1010888643369500742><:cchest2:1010888709031350333>\n<:cchest2:1010888756540215297><:cchest4:1010888875536822353> {common}",
                inline=True,
            )
            embed.add_field(
                name="Rare",
                value=f"<:rchest1:1010889168802562078><:rchest2:1010889239988277269>\n<:rchest3:1010889292672942101><:rchest4:1010889342639677560> {rare}",
                inline=True,
            )
            embed.add_field(
                name="Mythic",
                value=f"<:mchest1:1010889412558717039><:mchest2:1010889464119300096>\n<:mchest3:1010889506838302821><:mchest4:1010889554418487347> {mythic}",
                inline=True,
            )
            embed.add_field(
                name="Legend",
                value=f"<:lchest1:1010889611318411385><:lchest2:1010889654800756797>\n<:lchest4:1010889740138061925><:lchest3:1010889697687511080> {legend}",
                inline=True,
            )
            # This is for the purchased chest
            # This table is only made when players buy a chest
            # So new players won't have it causing command to fail
            if info is not None:
                rare_count = info.get("rare", 0)
                mythic_count = info.get("mythic", 0)
                legend_count = info.get("legend", 0)
                embed.add_field(name="Exalted", value=f"Count: {exalted}", inline=True)
                embed.add_field(
                    name="Purchased Chests",
                    value=f"Rare: {rare_count}/5\nMythic: {mythic_count}/5\nLegend: {legend_count}/5",
                    inline=True,
                )
            embed.set_footer(text=f"{interaction.user.name}'s Profile")
            try:
                await interaction.response.send_message(embed=embed, ephemeral=disabled)
            except:
                await interaction.followup.send(embed=embed, ephemeral=disabled)

        if self.view.choice == "Account Bound":
            async with interaction.client.db[0].acquire() as pconn:
                daycared = await pconn.fetchval(
                    "SELECT count(*) FROM pokes WHERE id = ANY ($1) AND pokname = 'Egg'",
                    self.player_data["pokes"],
                )
                usedmarket = await pconn.fetchval(
                    "SELECT count(id) FROM market WHERE owner = $1 AND buyer IS NULL",
                    interaction.user.id,
                )
            disabled = self.player_data["visible"]
            bike = self.player_data["bike"]
            dlimit = self.player_data["daycarelimit"]
            marketlimit = self.player_data["marketlimit"]
            iv_mult = self.bound_data["iv_multiplier"]
            shiny_mult = self.bound_data["shiny_multiplier"]
            breed_mult = self.bound_data["breeding_multiplier"]
            battle_mult = self.bound_data["battle_multiplier"]
            patreon_status = await interaction.client.patreon_tier(interaction.user.id)
            if patreon_status in ("Crystal Tier", "Sapphire Tier"):
                marketlimitbonus = CRYSTAL_PATREON_SLOT_BONUS
            elif patreon_status == "Silver Tier":
                marketlimitbonus = SILVER_PATREON_SLOT_BONUS
            elif patreon_status == "Yellow Tier":
                marketlimitbonus = YELLOW_PATREON_SLOT_BONUS
            elif patreon_status == "Red Tier":
                marketlimitbonus = PATREON_SLOT_BONUS
            else:
                marketlimitbonus = 0
            markettext = f"{usedmarket}/{marketlimit}"
            if marketlimitbonus:
                markettext += f" (+ {marketlimitbonus}!)"

            embed = discord.Embed(
                title=f"{interaction.user.name}'s Bound Items",
                description="These are items locked to your Discord account",
                color=0x0084FD,
            )
            embed.add_field(
                name="Misc",
                value=(
                    f"**Bicycle**: {bike}\n"
                    f"**Market Slots**: {markettext}\n"
                    f"**Daycare Slots**: {daycared}/{dlimit}\n"
                ),
                inline=True,
            )
            embed.add_field(
                name="Multipliers",
                value=(
                    f"**IV**: {calculate_iv_multiplier(iv_mult)}\n"
                    f"**Breeding**: {calculate_breeding_multiplier(breed_mult)}\n"
                    f"**Shiny**: {shiny_mult}\n"
                    f"**Battling**: {battle_mult}"
                ),
                inline=True,
            )
            embed.set_footer(text=f"{interaction.user.name}'s Profile")
            try:
                await interaction.response.send_message(embed=embed, ephemeral=disabled)
            except:
                await interaction.followup.send(embed=embed, ephemeral=disabled)

    # class ProfileView(discord.ui.View):
    """View that helps with Profile Menu"""

    def __init__(self, ctx, bound_data, bag_data, player_data):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.bag_data = bag_data
        self.bound_data = bound_data
        self.player_data = player_data
        self.event = asyncio.Event()
        self.message = ""
        self.add_item(DropdownSelect(bound_data, bag_data, player_data))

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
        pokes = self.player_data["pokes"]
        tnick = self.player_data["tnick"]
        count = len(pokes)
        region = self.player_data["region"]
        is_staff = self.player_data["staff"]
        credits = self.player_data["mewcoins"]
        redeems = self.player_data["redeems"]
        gleam_gems = self.bound_data["radiant_gem"]
        if is_staff.lower() != "user":
            staff_msg = f"\nMewbot Staff Member: **{is_staff.capitalize()}**"
        else:
            staff_msg = f"\nMewbot User"
        embed = discord.Embed(
            title=f"{self.ctx.author.name}'s Profile!",
            description=f"Trainer Nick: **{tnick}**{staff_msg}",
        )
        embed.add_field(
            name="General Info",
            value=(
                f"`Pokemon Caught`: {count:,}\n" f"`Active Region`: {region.title()}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Balances",
            value=(
                f"`Credits`: {credits:,}\n"
                f"`Redeems`: {redeems:,}\n"
                f"`Gleam Gems`: {gleam_gems:,}"
            ),
            inline=True,
        )
        embed.set_thumbnail(
            url="https://archives.bulbagarden.net/media/upload/3/3a/Spr_B2W2_Ace_Trainer_M.png"
        )
        embed.set_footer(text=f"{self.ctx.author.name}'s Profile")

        self.message = await self.ctx.send(embed=embed, view=self)
        await self.event.wait()


class ProfileView(discord.ui.View):
    """View that creates profile embed and displays buttons"""

    def __init__(self, ctx, bound_data, bag_data, player_data, badge_data):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.bag_data = bag_data
        self.bound_data = bound_data
        self.player_data = player_data
        self.badge_data = badge_data
        self.event = asyncio.Event()
        self.embed = ""

    # @discord.ui.Button(style=discord.ButtonStyle.red, label="Refresh", emoji="♺", row=2)
    # async def refresh(self, interaction, button):

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="Chests", emoji="<:legend_chest:1103389711424294942>", row=1
    )
    async def chests(self, interaction, button):
        await interaction.response.defer()

        # Output chest information and data
        # Hidden in database determines emphemeral status
        async with interaction.client.db[0].acquire() as pconn:
            info = await pconn.fetchrow(
                "SELECT rare, mythic, legend FROM cheststore WHERE u_id = $1",
                interaction.user.id,
            )
        disabled = self.player_data["visible"]
        # running chest totals
        common = self.bound_data["common_chest"]
        rare = self.bound_data["rare_chest"]
        mythic = self.bound_data["mythic_chest"]
        legend = self.bound_data["legend_chest"]
        exalted = self.bound_data["exalted_chest"]
        art = self.bound_data["art_chest"]
        embed = discord.Embed(
            title=f"{interaction.user}'s Chests",
            description="Chests hold various rewards! From credits to Pokemon.",
            color=0xFFB6C1,
        )
        embed.add_field(
            name="Normal Chests",
            value=(
                f"<:common_chest:1103387638544740482> **Common**\nCount: `{common}`\n"
                f"<:rare_chest:1103388951357706241> **Rare**\nCount: `{rare}`\n"
                f"<:mythic_chest:1103389973614436484> **Mythic**\nCount: `{mythic}`\n"
                f"<:legend_chest:1103389711424294942> **Legend**\nCount: `{legend}`\n"
            ),
            inline=True,
        )
        embed.add_field(
            name="Special Chests",
            value=(
                f"<:exalted_chest:1103389973614436484> **Exalted**\nCount: `{exalted}`\n"
                f"<:art_chest:1103389240949215384> **Art**\nCount: `{art}`"
            ),
            inline=True,
        )
        # This is for the purchased chest
        # This table is only made when players buy a chest
        # So new players won't have it causing command to fail
        if info is not None:
            rare_count = info.get("rare", 0)
            mythic_count = info.get("mythic", 0)
            legend_count = info.get("legend", 0)
            embed.add_field(
                name="Purchased Chests",
                value=f"Rare: {rare_count}/5\nMythic: {mythic_count}/5\nLegend: {legend_count}/5",
                inline=True,
            )
        embed.set_footer(text=f"{interaction.user.name}'s Profile | Exalted chest are no longer available.")
        await interaction.followup.send(embed=embed, ephemeral=disabled)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="Bound", emoji="🔑", row=1
    )
    async def bound(self, interaction, button):
        await interaction.response.defer()

        async with interaction.client.db[0].acquire() as pconn:
            daycared = await pconn.fetchval(
                "SELECT count(*) FROM pokes WHERE id = ANY ($1) AND pokname = 'Egg'",
                self.player_data["pokes"],
            )
            usedmarket = await pconn.fetchval(
                "SELECT count(id) FROM market WHERE owner = $1 AND buyer IS NULL",
                interaction.user.id,
            )
        disabled = self.player_data["visible"]
        bike = self.player_data["bike"]
        dlimit = self.player_data["daycarelimit"]
        marketlimit = self.player_data["marketlimit"]
        essence = self.player_data["essence"]

        iv_mult = self.bound_data["iv_multiplier"]
        shiny_mult = self.bound_data["shiny_multiplier"]
        breed_mult = self.bound_data["breeding_multiplier"]
        battle_mult = self.bound_data["battle_multiplier"]
        nature_caps = self.bound_data["nature_capsules"]
        honey = self.bound_data["honey"]
        vouchers = self.bound_data["vouchers"]
        patreon_status = await interaction.client.patreon_tier(interaction.user.id)
        if patreon_status in ("Crystal Tier", "Sapphire Tier"):
            marketlimitbonus = CRYSTAL_PATREON_SLOT_BONUS
        elif patreon_status == "Silver Tier":
            marketlimitbonus = SILVER_PATREON_SLOT_BONUS
        elif patreon_status == "Yellow Tier":
            marketlimitbonus = YELLOW_PATREON_SLOT_BONUS
        elif patreon_status == "Red Tier": 
            marketlimitbonus = PATREON_SLOT_BONUS
        else:
            marketlimitbonus = 0
        markettext = f"{usedmarket}/{marketlimit}"
        if marketlimitbonus:
            markettext += f" (+ {marketlimitbonus}!)"

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Bound Items",
            description="These are items locked to your Discord account",
            color=0x0084FD,
        )
        embed.add_field(
            name="Misc",
            value=(
                f"**Bicycle**: {bike}\n"
                f"**Market Slots**: {markettext}\n"
                f"**Daycare Slots**: {daycared}/{dlimit}\n"
                f"**Nature Capsules**: {nature_caps}\n"
                f"**Honey**: {honey}\n"
                f"**Vouchers**: {vouchers}\n"
                f"**Terastal Essence**:\n`X: {essence['x']}/25 | Y: {essence['y']}/50`"
            ),
            inline=True,
        )
        embed.add_field(
            name="Multipliers",
            value=(
                f"**IV**: `{iv_mult} - {calculate_iv_multiplier(iv_mult)}`\n"
                f"**Breeding**: `{breed_mult} - {calculate_breeding_multiplier(breed_mult)}`\n"
                f"**Shiny**: `{shiny_mult}`\n"
                f"**Battling**: `{battle_mult}`\n"
            ),
            inline=True,
        )
        embed.set_footer(text=f"{interaction.user.name}'s Profile")
        await interaction.followup.send(embed=embed, ephemeral=disabled)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="Shadow Hunts", emoji="<:shadow:1010559067590246410>", row=1,
    )
    async def shadow(self, interaction, button):
        await interaction.response.defer()

        disabled = self.player_data["visible"]
        hunt = self.player_data["hunt"]
        huntprogress = self.player_data["chain"]
        pokemon = hunt.capitalize()

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Shadow Hunt!",
            description="Shadows are special Pokemon with skins.\nThe higher your chain the more chances it'll spawn!",
            color=0x0084FD,
        )
        if hunt:
            embed.add_field(
                name=f"<:shadow:1010559067590246410> Details",
                value=(f"**Selected Hunt**: {hunt}\n" f"**Chain**: {huntprogress}x"),
                inline=False,
            )
        else:
            embed.add_field(
                name=f"Details",
                value=(f"**Selected Hunt**: Select with `/hunt`!"),
                inline=False,
            )
        # Get image for thumbnail
        embed.set_thumbnail(
            url=await get_pokemon_image(pokemon, interaction.client, skin="shadow")
        )

        embed.set_footer(
            text=f"{interaction.user.name}'s Profile | We are constantly uploading new Shadows!"
        )
        await interaction.followup.send(embed=embed, ephemeral=disabled)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="Badges", emoji="<:volcano:1146142634918817813>", row=1
    )
    async def badges(self, interaction, button):
        #patreon = await interaction.client.patreon_tier(interaction.user.id)
        #if patreon not in ("Crystal Tier", "Silver Tier", "Yellow Tier", "Red Tier") and interaction.guild.id == 998128574898896906:
            #await interaction.response.send_message("Coming soon!")
            #return
        GYM_LEADERS = await interaction.client.db[1].gym_leaders.find({}).to_list(None)
        leader_names = [t["identifier"] for t in GYM_LEADERS]
        column_names = [t["column"] for t in GYM_LEADERS]
        region_names = [t["region"] for t in GYM_LEADERS]
        badge_data = dict(self.badge_data)
        desc = ""
        count = 1
        for idx, name in enumerate(leader_names):
            # Index Region First
            region_name = region_names[idx]
            # Do Region Achievement First
            if count in [1, 9, 17, 25, 33, 41]:
                if badge_data[region_name] == True:
                    desc += f"🗺️ **{region_name.capitalize()}** Region Defeated: `True`\n\n"
                else:
                    desc += f"🗺️ **{region_name.capitalize()}** Region Defeated: `False`\n\n"

            # First pull badge name and emoji                    
            emoji, badge_name = get_badge_emoji(leader_name=column_names[idx])
            name = name.replace("_", " ").title()

            # Then format message depending on msg count
            if badge_data[column_names[idx]] is False:
                second_emoji = "`Locked` 🔒"
            else:
                second_emoji = "`Unlocked` 🔓"
            #if count in [8, 18]:
                #desc += f"**{name}**: {emoji} {badge_name.capitalize()} Badge  - {second_emoji}\n\n"
            #else:
                #desc += f"**{name}**: {emoji} {badge_name.capitalize()} Badge  - {second_emoji}\n"
            desc += f"**{name}**: {emoji} {badge_name.capitalize()} Badge  - {second_emoji}\n"
            count += 1
        footer_text = "Reach a 2 Win Streak in NPC Duels to challenge!"
        embed = discord.Embed(
            title="Gym Leader Badges!", color=3553600)
        pages = badge_pagify(desc, base_embed=embed, footer=footer_text)
        await SlashMenuView(interaction, pages).start()


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

    async def wait(self):
        """Returns the user's choice, or None if they did not choose in time."""
        # Start creating base embed
        pokes = self.player_data["pokes"]
        tnick = self.player_data["tnick"]
        count = len(pokes)
        region = self.player_data["region"]
        is_staff = self.player_data["staff"]
        credits = self.player_data["mewcoins"]
        redeems = self.player_data["redeems"]
        gleam_gems = self.bound_data["radiant_gem"]
        evpoints = self.player_data["evpoints"]
        visible = self.player_data["visible"]
        trainer_image = self.player_data["trainer_image"]
        if visible:
            hidden_text = "Private: True"
        else:
            hidden_text = "Private: False"
        if is_staff.lower() != "user":
            staff_msg = f"\nMewbot Staff Member: **{is_staff.title()}**"
        else:
            staff_msg = f"\nMewbot User"
        image_url = IMAGE_URLS.get(trainer_image)
        embed = discord.Embed(
            title=f"{self.ctx.author.name}'s Profile!",
            description=f"Trainer Nick: **{tnick}**{staff_msg}",
        )
        embed.add_field(
            name="General Info",
            value=(
                f"`Pokemon Caught`: {count:,}\n"
                f"`Active Region`: {region.title()}\n"
                f"`EV Points`: {evpoints:,} <:evs:1029331432792915988>"
            ),
            inline=True,
        )
        embed.add_field(
            name="Balances",
            value=(
                f"`Credits`: {credits:,} <:mewcoin:1010959258638094386>\n"
                f"`Redeems`: {redeems:,} <:redeem:1037942226132668417>\n"
                f"`Gleam Gems`: {gleam_gems:,} <a:radiantgem:774866137472827432>"
            ),
            inline=True,
        )
        embed.set_thumbnail(url=image_url)
        embed.set_footer(text=f"{self.ctx.author.name}'s Profile | {hidden_text}")

        self.message = await self.ctx.send(embed=embed, view=self)
        await self.event.wait()


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def profile(self, ctx):
        ...

    @profile.command(name="view")
    async def profile_view(self, ctx):
        """View your Player Profile"""
        staff_msg = ""
        # if ctx.author.id != 334155028170407949:
        # await ctx.send("This is locked for now")
        # return
        async with ctx.bot.db[0].acquire() as pconn:
            player_data = await pconn.fetchrow(
                "SELECT * FROM users WHERE u_id = $1", ctx.author.id
            )
            if player_data is None:
                await ctx.send("You haven't started yet!\nUse `/start` to begin.")
                return
            bag_data = await pconn.fetchrow(
                "SELECT * FROM bag WHERE u_id = $1", ctx.author.id
            )
            bound_data = await pconn.fetchrow(
                "SELECT * FROM account_bound WHERE u_id = $1", ctx.author.id
            )
            badge_data = await pconn.fetchrow(
                "SELECT * FROM achievements WHERE u_id = $1",
                ctx.author.id
            )
        if bag_data is None:
            await ctx.send(
                "Have you converted to the new bag system?\nUse `/bag convert` if you haven't!"
            )
            return
        if bound_data is None:
            await ctx.send(
                "Somehow you are missing an account bound entry!\nPlease report this in Mewbot Official!"
            )
            return
        await ProfileView(
            ctx, bound_data=bound_data, bag_data=bag_data, player_data=player_data, badge_data=badge_data
        ).wait()

    @profile.command(name="visible")
    async def profile_visible(self, ctx):
        """Sets the visiblility of your Profile"""
        async with ctx.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET visible = NOT visible WHERE u_id = $1", ctx.author.id
            )
        await ctx.send("Toggled profile visibility!")

    @profile.command(name="image")
    async def profile_image(self, ctx, category:Literal['xmas', 'halloween', 'summer', 'user', 'breeder'], name:str):
        """For managing profile images"""
        name = name.capitalize()
        async with ctx.bot.db[0].acquire() as pconn:
            images_inv = await pconn.fetchval(
                "SELECT trainer_images::json FROM account_bound WHERE u_id = $1",
                ctx.author.id
            )
            if images_inv is None:
                await ctx.send("You have not started!")
                return
            trainer_image = await pconn.fetchval(
                "SELECT trainer_image FROM users WHERE u_id = $1", 
                ctx.author.id
            )
            if trainer_image is None:
                await ctx.send("You have not started!")
                return
            if images_inv.get(category, {}).get(name, 0) < 1:
                await ctx.send(f"You do not have any {category} skins to display...")
                return
            confirm = (
                f"Are you sure you want to apply your {name} skin to your profile?\n"
            )
            if not await ConfirmView(ctx, confirm).wait():
                await ctx.send("Cancelling.")
                return

            #Add old one back to inventory
            old_category, old_name = trainer_image.split("/")
            new_skin_name = f"{category}/{name}"
            if old_category not in images_inv:
                images_inv[old_category] = {}
            images_inv[old_category][old_name] = images_inv[old_category].get(old_name, 0) + 1
            
            #Then remove the new one
            images_inv[category][name] -= 1
            await pconn.execute(
                "UPDATE account_bound SET trainer_images = $1::json WHERE u_id = $2",
                images_inv,
                ctx.author.id
            )
            await pconn.execute(
                "UPDATE users SET trainer_image = $1 WHERE u_id = $2",
                new_skin_name,
                ctx.author.id
            )

            await ctx.send(f"Successfully applied `{category}/{name}` skin to your profile page!")
            return




async def setup(bot):
    await bot.add_cog(Profile(bot))