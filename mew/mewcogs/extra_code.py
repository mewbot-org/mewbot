#Easter 2022 Code
    #@easter.command(name="list")
    async def easter_list(self, ctx):
        """View your easter eggs."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the easter season!")
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT * FROM eggs WHERE u_id = $1", ctx.author.id)
        if data is None:
            await ctx.send("You haven't found any eggs yet... Go find some!")
            return
        embed = discord.Embed(
            title=f"{ctx.author.name}'s eggs", color=0x6CB6E3)
        for idx, rarity in enumerate(("Common", "Uncommon", "Rare", "Legendary")):
            hold = ""
            owned = 0
            for egg in self.EGGS[idx]:
                if data[egg]:
                    hold += f"{self.EGG_EMOJIS[egg]} {egg.capitalize()} egg - {data[egg]}\n"
                    owned += 1
            if hold:
                embed.add_field(
                    name=f"{rarity} ({owned}/{len(self.EGGS[idx])})", value=hold)
        if not embed.fields:
            await ctx.send("You don't have any eggs right now... Go find some more!")
            return
        embed.set_footer(
            text=f"Use /easter buy to spend your eggs on a reward.")
        await ctx.send(embed=embed)

    #@easter.command(name="buy")
    async def easter_buy(self, ctx, choice: int = None):
        """Convert your eggs into various rewards."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the easter season!")
            return
        if choice is None:
            msg = (
                "**Egg rewards:**\n"
                "**1.** One of each common egg -> 10k credits + 1 common chest\n"
                "**2.** One of each uncommon egg -> 25k credits + 2 common chests\n"
                "**3.** One of each rare egg -> 50k credits + 1 rare chest\n"
                "**4.** One of each legendary egg -> 50k credits + 1 mythic chest\n"
                "**5.** One of each egg -> Easter Shuckle (one time per user) or 1 legend chest\n"
                f"Use `/easter buy <num>` to buy one of these rewards."
            )
            await ctx.send(msg)
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT * FROM eggs WHERE u_id = $1", ctx.author.id)
            inventory = await pconn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1", ctx.author.id
            )
        if inventory is None:
            await ctx.send(f"You haven't started!\nStart with `/start` first!")
            return
        if data is None:
            await ctx.send("You haven't found any eggs yet... Go find some!")
            return
        if choice == 1:
            if not all((data["bidoof"], data["caterpie"], data["pidgey"], data["magikarp"], data["spinarak"], data["tentacruel"], data["togepi"], data["bellsprout"])):
                await ctx.send("You do not have every common egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET bidoof = bidoof - 1, caterpie = caterpie - 1, pidgey = pidgey - 1, magikarp = magikarp - 1, "
                    "spinarak = spinarak - 1, tentacruel = tentacruel - 1, togepi = togepi - 1, bellsprout = bellsprout - 1 "
                    "WHERE u_id = $1", ctx.author.id
                )
                inventory["common chest"] = inventory.get(
                    "common chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 10000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 10k credits and 1 common chest.")
        elif choice == 2:
            if not all((data["ralts"], data["porygon"], data["farfetchd"], data["cubone"], data["omastar"], data["chansey"])):
                await ctx.send("You do not have every uncommon egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET ralts = ralts - 1, porygon = porygon - 1, farfetchd = farfetchd - 1, cubone = cubone - 1, "
                    "omastar = omastar - 1, chansey = chansey - 1 WHERE u_id = $1",
                    ctx.author.id
                )
                inventory["common chest"] = inventory.get(
                    "common chest", 0) + 2
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 25000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 25k credits and 2 common chests.")
        elif choice == 3:
            if not all((data["gible"], data["bagon"], data["larvitar"], data["dratini"])):
                await ctx.send("You do not have every rare egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET gible = gible - 1, bagon = bagon - 1, larvitar = larvitar - 1, dratini = dratini - 1 "
                    "WHERE u_id = $1",
                    ctx.author.id
                )
                inventory["rare chest"] = inventory.get("rare chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 50000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 50k credits and 1 rare chest.")
        elif choice == 4:
            if not all((data["kyogre"], data["dialga"])):
                await ctx.send("You do not have every legendary egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET kyogre = kyogre - 1, dialga = dialga - 1 WHERE u_id = $1",
                    ctx.author.id
                )
                inventory["mythic chest"] = inventory.get(
                    "mythic chest", 0) + 1
                await pconn.execute(
                    "UPDATE users SET mewcoins = mewcoins + 50000, inventory = $1::json WHERE u_id = $2",
                    inventory, ctx.author.id
                )
            await ctx.send("You have received 50k credits and 1 mythic chest.")
        elif choice == 5:
            if not all(data[x] for x in self.EGG_EMOJIS.keys()):
                await ctx.send("You do not have every egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET bidoof = bidoof - 1, caterpie = caterpie - 1, pidgey = pidgey - 1, magikarp = magikarp - 1, "
                    "spinarak = spinarak - 1, tentacruel = tentacruel - 1, togepi = togepi - 1, bellsprout = bellsprout - 1, "
                    "ralts = ralts - 1, porygon = porygon - 1, farfetchd = farfetchd - 1, cubone = cubone - 1, omastar = omastar - 1, "
                    "chansey = chansey - 1, gible = gible - 1, bagon = bagon - 1, larvitar = larvitar - 1, dratini = dratini - 1, "
                    "kyogre = kyogre - 1, dialga = dialga - 1, got_radiant = true WHERE u_id = $1",
                    ctx.author.id
                )
                if data["got_radiant"]:
                    inventory["legend chest"] = inventory.get(
                        "legend chest", 0) + 1
                    await pconn.execute(
                        "UPDATE users SET inventory = $1::json WHERE u_id = $2",
                        inventory, ctx.author.id
                    )
                    await ctx.send("You have received 1 legend chest.")
                else:
                    await ctx.bot.commondb.create_poke(ctx.bot, ctx.author.id, "Shuckle", skin="easter")
                    await ctx.send("You have received an Easter Shuckle! Happy Easter!")
        else:
            await ctx.send(f"That is not a valid option. Use `/easter buy` to see all options.")

    #@easter.command(name="convert")
    async def easter_convert(self, ctx, eggname: str = None):
        """Convert one of each egg from a lower tier to get an egg for a higher tier."""
        if not self.EASTER_COMMANDS:
            await ctx.send("This command can only be used during the easter season!")
            return
        if eggname is None:
            msg = (
                "**Convert one of each egg from a lower tier to a specific egg from a higher tier:**\n"
                "One of each common egg -> 1 uncommon egg\n"
                "One of each uncommon egg -> 1 rare egg\n"
                "One of each rare egg -> 1 legendary egg\n"
                f"Use `/easter convert <eggname>` to convert your eggs."
            )
            await ctx.send(msg)
            return
        eggname = eggname.lower()
        if eggname in self.EGGS[0]:
            await ctx.send("You cannot convert to a common egg!")
            return
        async with self.bot.db[0].acquire() as pconn:
            data = await pconn.fetchrow("SELECT * FROM eggs WHERE u_id = $1", ctx.author.id)
        if data is None:
            await ctx.send("You haven't found any eggs yet... Go find some!")
            return
        # common -> uncommon
        if eggname in self.EGGS[1]:
            if not all((data["bidoof"], data["caterpie"], data["pidgey"], data["magikarp"], data["spinarak"], data["tentacruel"], data["togepi"], data["bellsprout"])):
                await ctx.send("You do not have every common egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET bidoof = bidoof - 1, caterpie = caterpie - 1, pidgey = pidgey - 1, magikarp = magikarp - 1, "
                    f"spinarak = spinarak - 1, tentacruel = tentacruel - 1, togepi = togepi - 1, bellsprout = bellsprout - 1, {eggname} = {eggname} + 1"
                    "WHERE u_id = $1", ctx.author.id
                )
            await ctx.send(f"Successfully converted one of every common egg into a {eggname} egg!")
        # uncommon -> rare
        elif eggname in self.EGGS[2]:
            if not all((data["ralts"], data["porygon"], data["farfetchd"], data["cubone"], data["omastar"], data["chansey"])):
                await ctx.send("You do not have every uncommon egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    "UPDATE eggs SET ralts = ralts - 1, porygon = porygon - 1, farfetchd = farfetchd - 1, cubone = cubone - 1, "
                    f"omastar = omastar - 1, chansey = chansey - 1, {eggname} = {eggname} + 1 WHERE u_id = $1",
                    ctx.author.id
                )
            await ctx.send(f"Successfully converted one of every uncommon egg into a {eggname} egg!")
        # rare -> legendary
        elif eggname in self.EGGS[3]:
            if not all((data["gible"], data["bagon"], data["larvitar"], data["dratini"])):
                await ctx.send("You do not have every rare egg yet... Keep searching!")
                return
            async with self.bot.db[0].acquire() as pconn:
                await pconn.execute(
                    f"UPDATE eggs SET gible = gible - 1, bagon = bagon - 1, larvitar = larvitar - 1, dratini = dratini - 1, {eggname} = {eggname} + 1 "
                    "WHERE u_id = $1",
                    ctx.author.id
                )
            await ctx.send(f"Successfully converted one of every rare egg into a {eggname} egg!")
        else:
            await ctx.send("That is not a valid egg name!")
            return