import discord
from discord.ext import tasks, commands
import time
from datetime import datetime, timedelta
import random


# Lord only knows why this is here or what it does...
class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Mother(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if self.bot.cluster["id"] == 1:
            self.mother.start()
            self.energy.start()
            self.npc_energy.start()
            self.berries.start()
            self.hatch_incubators.start()

    @tasks.loop(seconds=10)  # Runs every week
    async def deduct_market_fees(self):
        current_date = datetime.now()
        one_week_ago = current_date - timedelta(days=7)

        try:
            async with self.bot.db[0].acquire() as conn:
                # Fetch listings older than a week
                sql = """
                    SELECT poke, owner, price
                    FROM market
                    WHERE listed_date < $1;
                """
                rows = await conn.fetch(sql, one_week_ago)

            # Deduct fees for each retrieved slot
            for poke, owner, price in rows:
                fee = price * 0.01
                try:
                    # Update user's credits
                    sql = "UPDATE users SET mewcoins = mewcoins - $1 WHERE u_id = $2"
                    await conn.execute(sql, fee, owner)
                    print(
                        f"Deducted market fee of {fee} credits from {owner} (Market ID: {poke})."
                    )
                except Exception as e:
                    print(f"Error deducting fee for slot {poke}: {e}")

        except Exception as e:
            print(f"Error checking and deducting fees: {e}")

    @tasks.loop(seconds=1440)
    async def energy(self):
        async with self.bot.db[0].acquire() as pconn:
            # DELETE HONEY
            await pconn.execute(
                "DELETE FROM honey WHERE expires < EXTRACT(EPOCH FROM CURRENT_TIMESTAMP);"
            )
            await pconn.execute(
                "UPDATE users SET energy = energy + 1 WHERE energy < 10"
            )

    @tasks.loop(minutes=30)
    async def npc_energy(self):
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute(
                "UPDATE users SET npc_energy = LEAST(npc_energy + 5, 10) WHERE npc_energy < 10;"
            )

    @tasks.loop(seconds=300)
    async def berries(self):
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE berries SET ready = True")
    
    @tasks.loop(hours=1)
    async def hatch_incubators(self):
        async with self.bot.db[0].acquire() as pconn:
            await pconn.execute("UPDATE pokes SET pokname = name WHERE incubate_for < NOW() + INTERVAL '6 hours'")
            await pconn.execute("UPDATE pokes SET incubate_for = NULL WHERE incubate_for < NOW() + INTERVAL '6 hours'")

    @tasks.loop(seconds=60 * 10)
    async def mother(self):
        primary_key = random.choice(list(self.bot.primaries.keys()))
        primary_value = self.bot.primaries[primary_key][1]
        secondary_key = random.choice(list(self.bot.secondaries.keys()))
        secondary_value = self.bot.secondaries[secondary_key][1]
        existing = await self.bot.db[1].missions.find_one()
        if not existing:
            insert = {
                "createdAt": datetime.now(),
                "missions": [
                    [primary_key, random.randint(1, primary_value)],
                    [secondary_key, random.randint(1, secondary_value)],
                ],
            }
            # Add the new mission reqs
            await self.bot.db[1].missions.insert_one(insert)
            # Reset the missions progress for all users
            await self.bot.db[1].users.delete_many({})

    def cog_unload(self):
        self.energy.cancel()
        self.npc_energy.cancel()
        self.mother.cancel()
        self.berries.cancel()
        self.hatch_incubators.cancel()


async def setup(bot):
    await bot.add_cog(Mother(bot))
