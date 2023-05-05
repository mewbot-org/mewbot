import discord
import asyncio
import datetime
import random

from discord import ui
from discord.ext import commands

from typing import Literal
#from mewcogs.pokemon_list import berryList
from mewutils.misc import get_berry_emoji, get_farm_thumbnail, ConfirmView

class FertilizeView(discord.ui.View):
    """Provides users with base fertilizing embed"""
    def __init__(self,
                ctx,
                user_id,
                berry_ids,
                berry_names,
                fertilizers,
                fertilizer_quantity,
                emojis,
                first_embed
        ):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.farmer = user_id
        self.berry_ids = berry_ids
        self.berry_names = berry_names
        self.fertilizers = fertilizers
        self.fertilizer_quantity = fertilizer_quantity
        self.emojis = emojis
        self.first_embed = first_embed
        self.event = asyncio.Event()
        self.add_item(DropdownSelectFertilize(berry_ids, berry_names, fertilizers, fertilizer_quantity, emojis))

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
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
        self.message = await self.ctx.send(embed=self.first_embed, view=self)
        await self.event.wait()

class DropdownSelectFertilize(discord.ui.Select):
    def __init__(self, berry_ids, berry_names, fertilizers, fertilizer_quantity, emojis):
        self.berry_ids = berry_ids
        self.fertilizers = fertilizers
        self.fertilizer_quantity = fertilizer_quantity
        self.berry_names = berry_names
        self.emojis = emojis

        length = len(berry_ids)
        count = 0
        options = []

        for idx in range(length):
            num = idx + 1
            berry_name = self.berry_names[idx].replace("_", " ").title()
            emoji = self.emojis[idx]
            fertilized = self.fertilizers[idx]
            add = False

            if fertilized == False:
                add = True
                msg = "Fertilize this berry!"

            if add:
                options.append(
                    discord.SelectOption(
                        label=f"{num}. {berry_name}",
                        description=f"{msg}",
                        emoji=f"{emoji}"
                    )
            )
        super().__init__(placeholder='Pick a berry...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = interaction.data['values'][0]
        optnum = int(self.view.choice[0]) - 1
        berry_id = self.berry_ids[optnum]
        berry_name = self.berry_names[optnum]
        fertilizer_count = self.fertilizer_quantity
        berry_thumbnail = get_farm_thumbnail(
            name = berry_name.title()
        )

        async with interaction.client.db[0].acquire() as pconn:
            #Apply fertilizer to berry
            await pconn.execute(
                "UPDATE berries SET fertilized = True WHERE berry_id = $1",
                berry_id
            )
            await pconn.execute(
                "UPDATE bag SET fertilizer = fertilizer - 1 WHERE u_id = $1",
                interaction.user.id
            )
            msg = "Your berry has been fertilized!\nCheck on it frequently."

        berry_name = berry_name.replace("_", " ").title()
        embed = discord.Embed(
            title=f"{interaction.user.name}'s {berry_name}",
            description=f"{msg}",
            color=0x03FC85
        )
        embed.set_thumbnail(url=berry_thumbnail)
        if (len(self.options) - 1) <= 0:
            self.disabled = True
        else:
            opt = discord.utils.get(self.options, value=interaction.data['values'][0])
            self.options.remove(opt)

        await interaction.response.edit_message(view=self.view)
        #await asyncio.sleep(2)
        await interaction.followup.send(embed=embed, ephemeral=True)


class FarmView(discord.ui.View):
    """Provides user with base farm embed"""
    def __init__(self, 
                ctx, 
                user_id, 
                berry_ids, 
                berry_names, 
                intervals, 
                statuses,
                fertilizers, 
                emojis,
                water_tank,
                player_data, 
                first_embed
        ):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.farmer = user_id
        self.berry_ids = berry_ids
        self.berry_names = berry_names
        self.intervals = intervals
        self.statuses = statuses
        self.fertilizers = fertilizers
        self.emojis = emojis
        self.water_tank = water_tank
        self.player_data = player_data
        self.first_embed = first_embed
        self.event = asyncio.Event()
        self.add_item(DropdownSelect(berry_ids, berry_names, statuses, fertilizers, intervals, emojis, water_tank))
    
    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(content="You are not allowed to interact with this button.", ephemeral=True)
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
        self.message = await self.ctx.send(embed=self.first_embed, view=self)
        await self.event.wait()
        

class DropdownSelect(discord.ui.Select):
    def __init__(self, berry_ids, berry_names, statuses, fertilizers, intervals, emojis, water_tank):
        self.berry_ids = berry_ids
        self.intervals = intervals
        self.statuses = statuses
        self.fertilizers = fertilizers
        self.berry_names = berry_names
        self.emojis = emojis
        self.water_tank = water_tank

        length = len(berry_ids)
        count = 0
        options = []

        for idx in range(length):
            num = idx + 1
            berry_name = self.berry_names[idx].replace("_", " ").title()
            status = self.statuses[idx]
            emoji = self.emojis[idx]
            interval = self.intervals[idx]

            if status == True:
                if self.water_tank - 1 > 0:
                    add = True
                    msg = "Water this berry!"
            elif interval <= 0:
                msg = "Harvest this berry!"
                add = True
            else:
                add = False

            if add:
                options.append(
                    discord.SelectOption(
                        label=f"{num}. {berry_name}",
                        description=f"{msg}",
                        emoji=f"{emoji}"
                    )
            )
        super().__init__(placeholder='Pick a berry...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = interaction.data['values'][0]
        optnum = int(self.view.choice[0]) - 1
        berry_id = self.berry_ids[optnum]
        berry_name = self.berry_names[optnum]
        interval = self.intervals[optnum]
        fertilized = self.fertilizers[optnum]
        berry_thumbnail = get_farm_thumbnail(
            name = berry_name.title()
        )
        print(interaction.data)
        print(self.options)

        async with interaction.client.db[0].acquire() as pconn:
            #Berry should be delete from table and given to player
            if fertilized:
                amount_gained = random.randint(2, 3)
            else:
                amount_gained = 1
            if interval <= 0:
                #Remove from table and give user berry
                await pconn.execute(
                    "DELETE FROM berries WHERE berry_id = $1 and u_id = $2",
                    berry_id,
                    interaction.user.id
                )
                await interaction.client.commondb.add_bag_item(
                    interaction.user.id,
                    berry_name,
                    amount_gained 
                )
                msg = f"Your berry has reached full maturity!\nYou put the berry into your bag."
            else:
                await pconn.execute(
                    "UPDATE berries SET intervals = intervals - 1, ready = False WHERE berry_id = $1 AND u_id = $2",
                    berry_id,
                    interaction.user.id
                )
                await pconn.execute(
                    "UPDATE bag SET water_tank = water_tank - 1 WHERE u_id = $1",
                    interaction.user.id
                )
                msg = "Your berry is one step closer to being fully grown!\nCheck on it frequently."

        berry_name = berry_name.replace("_", " ").title()
        embed = discord.Embed(
            title=f"{interaction.user.name}'s {berry_name}",
            description=f"{msg}",
            color=0x03FC85
        )
        embed.set_thumbnail(url=berry_thumbnail)
        if (len(self.options) - 1) <= 0:
            self.disabled = True
        else:
            opt = discord.utils.get(self.options, value=interaction.data['values'][0])
            self.options.remove(opt)

        await interaction.response.edit_message(view=self.view)
        #await asyncio.sleep(2)
        await interaction.followup.send(embed=embed, ephemeral=True)

class Farming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def farm(self, ctx):
        pass

    @farm.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def plant(self, ctx, berry: Literal["Aguav", "Figy", "Iapapa", "Mago", "Wiki", "Sitrus", "Apicot", "Ganlon", "Lansat", "Liechi", "Micle", "Petaya", "Salac", "Starf", "Aspear", "Cheri", "Chesto", "Lum", "Pecha", "Persim", "Rawst"], amount:int):
        """Plants a new berry in one of the plots alloted"""
        async with ctx.bot.db[0].acquire() as pconn:
            landplots = await pconn.fetchval(
                "SELECT landplots FROM users WHERE u_id = $1",
                ctx.author.id
            )
            bag = await pconn.fetchrow(
                "SELECT * FROM bag WHERE u_id = $1",
                ctx.author.id
            )
            active_task_count = await pconn.fetchval(
                "SELECT COUNT(u_id) FROM berries WHERE u_id = $1",
                ctx.author.id
            )

        #Make sure they don't use too much
        if active_task_count + amount > landplots:
            await ctx.send("Sorry, you are using all of your plots.")
            return
        
        #Proceed with removing seed from inventory 
        #And then adding berry to task table
        bag = dict(bag)
        seed_name = f"{berry.lower()}_seed"
        berry_name = f"{berry.lower()}_berry"
        intervals = 5
        current_seed_amount = bag[seed_name]

        if (current_seed_amount - amount) < 0:
            await ctx.send(f"Sorry you don't have enough {berry} Seeds.")
            return
        await self.bot.commondb.remove_bag_item(
            ctx.author.id,
            seed_name,
            amount
        )
        async with ctx.bot.db[0].acquire() as pconn:
            for i in range(amount):
                print(f"added {i} berries")
                query = "INSERT INTO berries (u_id, intervals, berry_name) VALUES ($1, $2, $3)"
                args = (
                    ctx.author.id,
                    intervals,
                    berry_name,
                )
                await pconn.execute(query, *args)
        await ctx.send(f"You've successfully planted {amount}x {berry} Berries!\nMake sure to water it using `/farm info`!")

    @farm.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def info(self, ctx):
        """Take a look at your farm!"""
        async with self.bot.db[0].acquire() as pconn:
            berry_data = await pconn.fetch(
                "SELECT * FROM berries WHERE u_id = $1",
                ctx.author.id
            )
            player_data = await pconn.fetchrow(
                "SELECT water_tank, fertilizer FROM bag WHERE u_id = $1",
                ctx.author.id
            )
            landplots = await pconn.fetchval(
                "SELECT landplots FROM users WHERE u_id = $1",
                ctx.author.id
            )
        water_tank = player_data['water_tank']
        fertilizer = player_data['fertilizer']

        if water_tank <= 0:
            await ctx.send("Your water tank is empty!\nUse `/buy item water tank` to fill it!")
            return

        if len(berry_data) == 0:
            first_embed = discord.Embed(
                title=f"{ctx.author.name}'s Farm!",
                description=f"Each button below simulates a landplot!\n🚰 `Water Tank`: {water_tank} / 10\n<:fertilizer:1097357605690675251> `Fertilizer`: {fertilizer}",
                color=0x03FC85
            )
            first_embed.set_thumbnail(
                url="https://archives.bulbagarden.net/media/upload/6/61/Spr_DP_Rancher.png"
            )
            first_embed.set_footer(
                text="/farm plant to plant some seeds!"
            )
            for i in range(1, landplots):
                first_embed.add_field(
                    name=f"Plot {i}",
                    value="Empty",
                    inline=True
                )
            await ctx.send(embed=first_embed)
            return

        berry_ids = [record['berry_id'] for record in berry_data]
        berry_names = [record['berry_name'] for record in berry_data]
        intervals = [record['intervals'] for record in berry_data]
        statuses = [record['ready'] for record in berry_data]
        fertilizers = [record['fertilized'] for record in berry_data]
        emojis = []

        first_embed = discord.Embed(
            title=f"{ctx.author.name}'s Farm!",
            description=f"Each button below simulates a landplot!\n🚰 `Water Tank`: {water_tank} / 10\n<:fertilizer:1097357605690675251> `Fertilizer`: {fertilizer}",
            color=0x03FC85
        )
        first_embed.set_thumbnail(
            url="https://archives.bulbagarden.net/media/upload/6/61/Spr_DP_Rancher.png"
        )
        first_embed.set_footer(
            text="Use the dropdown menu to water/pick your berries"
        )
        length = len(berry_ids)
        for idx in range(length):
            num = idx + 1
            berry_id = berry_ids[idx]
            berry_name = berry_names[idx].title()
            interval = intervals[idx]
            status = statuses[idx]
            berry_url = get_berry_emoji(
                name=berry_name
            )
            emojis.append(berry_url)
            berry_name = berry_name.replace("_", " ")
            if interval == 0:
                interval = "Matured"

            first_embed.add_field(
                name = f"{num}. {berry_name} {berry_url}",
                value = f"`Waters`: {interval}\n`Ready`: {status}",
                inline=True
            )

        #If all berries are ready and view is sent it'll crash
        if True not in statuses:
            await ctx.send(embed=first_embed)
            return

        await FarmView(
            ctx,
            ctx.author.id,
            berry_ids,
            berry_names,
            intervals,
            statuses,
            fertilizers,
            emojis,
            water_tank,
            player_data,
            first_embed
        ).wait()

    @farm.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fertilize(self, ctx):
        """Fertilize a berry!"""
        async with self.bot.db[0].acquire() as pconn:
            berry_data = await pconn.fetch(
                "SELECT * FROM berries WHERE u_id = $1",
                ctx.author.id
            )
            fertilizer = await pconn.fetchval(
                "SELECT fertilizer FROM bag WHERE u_id = $1",
                ctx.author.id
            )
            landplots = await pconn.fetchval(
                "SELECT landplots FROM users WHERE u_id = $1",
                ctx.author.id
            )

        #If they don't have any berries growing
        if len(berry_data) == 0:
            first_embed = discord.Embed(
                title=f"{ctx.author.name}'s Farm!",
                description=f"Each button below simulates a landplot!\n<:fertilizer:1097357605690675251> `Fertilizer`: {fertilizer}",
                color=0x03FC85
            )
            first_embed.set_thumbnail(
                url="https://archives.bulbagarden.net/media/upload/6/61/Spr_DP_Rancher.png"
            )
            first_embed.set_footer(
                text="/farm plant to plant some seeds!"
            )
            for i in range(1, landplots):
                first_embed.add_field(
                    name=f"Plot {i}",
                    value="Empty",
                    inline=True
                )
            await ctx.send(embed=first_embed)
            return

        #There are berries growing, process data
        berry_ids = [record['berry_id'] for record in berry_data]
        berry_names = [record['berry_name'] for record in berry_data]
        fertilizers = [record['fertilized'] for record in berry_data]
        emojis = []

        first_embed = discord.Embed(
            title=f"{ctx.author.name}'s Farm!",
            description=f"Each button below simulates a landplot!\n<:fertilizer:1097357605690675251> `Fertilizer`: {fertilizer}",
            color=0x03FC85
        )
        first_embed.set_thumbnail(
            url="https://archives.bulbagarden.net/media/upload/6/61/Spr_DP_Rancher.png"
        )
        first_embed.set_footer(
            text="Use the dropdown menu to water/pick your berries"
        )
        length = len(berry_ids)
        if length != 0:
            for idx in range(length):
                num = idx + 1
                #berry_id = berry_ids[idx]
                berry_name = berry_names[idx].title()
                fertilized = fertilizers[idx]
                user_fertilizer = fertilizer
                if fertilized:
                    check_status = "✅"
                elif user_fertilizer - 1 < 0:
                    check_status = "❎ - No Fertilizer"
                else:
                    check_status = "❎"

                berry_url = get_berry_emoji(
                    name=berry_name
                )
                emojis.append(berry_url)
                berry_name = berry_name.replace("_", " ")

                first_embed.add_field(
                    name = f"{num}. {berry_name} {berry_url}",
                    value = f"`Fertilized`: {check_status}",
                    inline=True
                )

                #Since we added embed, user more likely than not going to furtilzie.
                #Subtract from user_fertilizer so that next plot properly displays no fertilizer message.
                user_fertilizer -= 1
        else:
            await ctx.send(embed=first_embed)
            return

        #If all berries are fertilized and view is sent it'll crash
        #If user's total fertilizer would be under or equal to 0 don't send view
        if False not in tuple(fertilizers) or user_fertilizer <= 0:
            await ctx.send(embed=first_embed)
            return

        await FertilizeView(
            ctx,
            ctx.author.id,
            berry_ids,
            berry_names,
            fertilizers,
            fertilizer,
            emojis,
            first_embed
        ).wait()


async def setup(bot):
    await bot.add_cog(Farming(bot))
