import discord
import asyncio

from discord.ext import commands
from typing import Literal

breeding_thresholds = [250, 500, 1000]

def threshold_check(new_count:int, current_count:int=0):
    level_up = False
    if new_count >= 1000:
        treshold = 1000
        if current_count < 1000:
            msg = "You've reached Ranked 3"
            level_up = True
        else:
            msg = "<:levelthree:1128781839868370994>"
    elif new_count >= 500:
        treshold = 500
        if current_count < 500:
            msg = "You've reached Ranked 2"
            level_up = True
        else:
            msg = "<:leveltwo:1128781838589112320>"
    elif new_count >= 250:
        treshold = 250
        if current_count < 250:
            msg = "You've reached Ranked 1"
            level_up = True
        else:
            msg = "<:leveone:1128781836500336702>"
    else:
        treshold = 250 #Means locked
        msg = "🔒"
    return treshold, msg, level_up

class ListSelectBreeding(discord.ui.Select):
    """Drop down selection for trainer image"""
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Breeder1",
                emoji="<:breeder1:1196868278056923328>"
            ),
            discord.SelectOption(
                label="Breeder2",
                emoji="<:breeder2:1196868276014297158>"
            )
        ]
        super().__init__(
            options=options
        )

    async def callback(self, interaction):
        self.view.choice = interaction.data["values"][0]
        self.view.event.set()

class ListSelectView(discord.ui.View):
    """View to handle trainer selection"""
    def __init__(self, ctx, confirm_content: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.choice = None
        self.event = asyncio.Event()
        self.confirm_content = confirm_content
        self.add_item(ListSelectBreeding())

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
        self.event.set()

    async def on_error(self, interaction, error, item):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def wait(self):
        """Returns the user's choice, or None if they did not choose in time."""
        self.message = await self.ctx.send(self.confirm_content, view=self)
        await self.event.wait()
        return self.choice

class Achievements(commands.Cog):
    """Handles Achievement System"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_egg_born(self, channel, user, achievement:str=None, gained_count:int=1):
        if self.bot.botbanned(user.id):
            return
        async with self.bot.db[0].acquire() as pconn:
            print("Triggered Breed Achievement Event")
            await pconn.execute(
                "INSERT INTO achievements (u_id) VALUES ($1) ON CONFLICT DO NOTHING", 
                user.id
            )
            achievement_data = await pconn.fetchrow(
                "SELECT breed_titan, breed_penta, breed_success FROM achievements WHERE u_id = $1",
                user.id
            )
            current_count = int(achievement_data[f'{achievement}'])
            new_count = current_count + 1

            #Update achievement with new amount
            #Not good but it's set values ...
            if achievement != "breed_success": 
                await pconn.execute(
                    f"UPDATE achievements SET {achievement} = {achievement} + 1, breed_success = breed_success + 1 WHERE u_id = $1",
                    user.id
                )
            else:
                await pconn.execute(
                    "UPDATE achievements SET breed_success = breed_success + 1 WHERE u_id = $1",
                    user.id
                )
            #Send this info over and check if it should be a level up
            #Most likely it will be , so send embed as well
            threshold, msg, level_up = threshold_check(new_count=new_count, current_count=current_count)
            if level_up:
                achievement_msg = achievement.replace("_", " ").title()
                embed = discord.Embed(
                    title="⭐ Achievement Complete!",
                    description=f"Congrats! {msg} in the {achievement_msg} Achievement. 🎊",
                    color=0x0084FD
                )
                await channel.send(embed=embed)
                return

    @commands.hybrid_group()
    async def achievements(self, ctx:commands.Context):
        ...

    @achievements.command(name="breeding")
    async def achievements_breeding(self, ctx):
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Coming soon")
            #return
        achievement_list = ["breed_titan", "breed_penta", "breed_success"]
        async with ctx.bot.db[0].acquire() as pconn:
            achievement_data = await pconn.fetchrow(
                "SELECT breed_titan, breed_penta, breed_success FROM achievements WHERE u_id = $1",
                ctx.author.id
            )
            if achievement_data is None:
                achievement_data = []

        #Throw achievement data into Dict
        achievement_data = dict(achievement_data)

        embed = discord.Embed(
            title="Breeding Achievements!",
            description="These are unlocked through our breeding command.",
            color=0x0084FD
        )
        if len(achievement_data) != 0:
            for i in range(0, 3):
                achieve_name = achievement_list[i]
                current_threshold = achievement_data[achieve_name]
                thresold, msg, level_up = threshold_check(new_count=current_threshold, current_count=current_threshold)
                achievement_msg = achieve_name.replace("_", " ").title()
                    
                embed.add_field(
                    name=f"{achievement_msg}",
                    value=f"`Count`: {achievement_data[achieve_name]} / {thresold}\n`Rank:`{msg}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
                    
    @achievements.command(name="claim")
    async def achievements_claim(self, ctx, category: Literal['Breeding']):
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Currently under maintenance")
            #return
        #For now it's just breeding achievements,
        #Eventually will need to add to category above
        msg = ""
        if category == 'Breeding':
            async with ctx.bot.db[0].acquire() as pconn:
                trainer_images = await pconn.fetchval(
                    "SELECT trainer_images::json FROM account_bound WHERE u_id = $1",
                    ctx.author.id
                )
                breed_success = await pconn.fetchval(
                    "SELECT breed_success FROM achievements WHERE u_id = $1",
                    ctx.author.id
                )
            #For the time being we only offer a reward on the "successful breeds"
            if breed_success >= 250:
                if "breeder" in trainer_images:
                    await ctx.send("You've already claimed the 250 successful breeds reward!")
                    return
                choice = await ListSelectView(
                    ctx, "Please choose a trainer image!"
                ).wait()
                if choice is None:
                    await ctx.send("You did not select in time, cancelling.")
                    self.purchaselock.remove(ctx.author.id)
                    return
                choice = str(choice)
                category = "breeder"
                if category not in trainer_images:
                    trainer_images[category] = {}
                if choice not in trainer_images[category]:
                    trainer_images[category][choice] = 1
                else:
                    trainer_images[category][choice] += 1
                async with ctx.bot.db[0].acquire() as pconn:
                    await pconn.execute(
                        "UPDATE account_bound SET trainer_images = $1::json WHERE u_id = $2",
                        trainer_images,
                        ctx.author.id
                    )
                msg += f"You've successfully redeemed {choice} as your trainer image!\nIt's been added to your trainer image inventory."
            await ctx.send(f"{msg}")

async def setup(bot):
    await bot.add_cog(Achievements(bot))