import discord

from discord.ext import commands

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
        if ctx.author.id != 334155028170407949:
            await ctx.send("Coming soon")
            return
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
                    

async def setup(bot):
    await bot.add_cog(Achievements(bot))