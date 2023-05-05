import discord
import asyncio

from discord import app_commands
from discord.ext import commands
from mewutils.misc import get_battle_emoji, get_trade_emoji, get_stone_emoji, get_form_emoji, pagify, SlashMenuView, MenuView

class DropdownSelect(discord.ui.Select):
    def __init__(self, bag_data):
        options = [
            discord.SelectOption(label="General", description="General Items, Crystals, Vitamins", emoji='<:general_items:1093297547805720576>'),
            discord.SelectOption(label="Evostones", description="Type and Mega stones", emoji='<:powerup:672623832514822189>'),
            discord.SelectOption(label="Trades", description="Items held during trades", emoji='<:general:672627507278905355>'),
            discord.SelectOption(label="Plates and Memories", description="Items for Arceus and Silvally", emoji='<:crystalsbag:682684746911973392>'),
            discord.SelectOption(label="Forms", description="Change Pokemon forms", emoji='<:tradeitems:672816581897748480>'),
            discord.SelectOption(label="Battles", description="Used by Pokemon during duels", emoji='<:battlebag:674293206690562099>'),
            discord.SelectOption(label="Berries", description="Berries gained through farming", emoji='<:bag_berry:741137148316614696>'),
        ]
        self.bag_data = bag_data
        self.bag_data_dict = dict(bag_data)
        super().__init__(placeholder='Make your selection...', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.choice = interaction.data['values'][0]
        
        if self.view.choice == 'Evostones':
            sunstone = self.bag_data['sun_stone']
            thunderstone = self.bag_data['thunder_stone']
            shinystone = self.bag_data['shiny_stone']
            leafstone = self.bag_data['leaf_stone']
            duskstone = self.bag_data['dusk_stone']
            dawnstone = self.bag_data['dawn_stone']
            icestone = self.bag_data['ice_stone']
            firestone = self.bag_data['fire_stone']
            waterstone = self.bag_data['water_stone']
            ovalstone = self.bag_data['oval_stone']
            moonstone = self.bag_data['moon_stone']
            megastone_x = self.bag_data['mega_stone_x']
            megastone_y = self.bag_data['mega_stone_y']
            megastone = self.bag_data['mega_stone']
            everstone = self.bag_data['everstone']

            embed = discord.Embed(
                title=f"Evolution Stones", 
                description=f"These items help certain Pokemon evolve!", 
                color=0x0084FD
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:sunstone:669922327085187083> **Sun Stone**: {sunstone}"
                    f"\n<:moonstone:669922327168942101> **Moon Stone**: {moonstone}"
                    f"\n<:waterstone:669922327332388875> **Water Stone**: {waterstone}"
                    f"\n<:thunderstone:669922327248633856> **Thunder Stone**: {thunderstone}"
                    f"\n<:shinystone:669922327261347870> **Shiny Stone**: {shinystone}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:leafstone:669922327189913601> **Leaf Stone**: {leafstone}"
                    f"\n<:duskstone:669922327227793448> **Dusk Stone**: {duskstone}"
                    f"\n<:dawnstone:669922327173267462> **Dawn Stone**: {dawnstone}"
                    f"\n<:ovalstone:713196958935810059> **Oval Stone**: {ovalstone}"
                    f"\n<:icestone:669922326686728226> **Ice Stone**: {icestone}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:firestone:669922326971940875> **Fire Stone**: {firestone}"
                    f"\n<:mega_stone:1085424851277324379> **Mega Stone**: {megastone}"
                    f"\n<:mega_stone_x:1085424853785518151> **Mega Stone X**: {megastone_x}"
                    f"\n<:mega_stone_y:1085424852141346878> **Mega Stone Y**: {megastone_y}"
                    f"\n<:everstone:676820212741308451> **Everstone**: {everstone}"
                ),
                inline=True
            )
            embed.set_footer( 
                text=f"{interaction.user.name}'s bag"
            )
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == 'Trades':
            TRADE_ITEMS = await interaction.client.db[1].trade_items.find({}).to_list(None)
            items = [t["item"] for t in TRADE_ITEMS]
            desc = ""
            count = 1
            for idx, item in enumerate(items):
                emoji = get_trade_emoji(
                    item_name=item.lower()
                )
                amount = self.bag_data_dict[item]
                #So on each of these items essentially page break
                if count in [7, 14, 21]: 
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`Amount`: {amount:,}\n\n"
                else:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`Amount`: {amount:,}\n"
                count += 1
            #footer_text = "Each item is 3,000 credits"
            embed = discord.Embed(
                title="Held Items for Trades!", color=3553600)
            #pages = pagify(desc, base_embed=embed, footer=footer_text)
            pages = pagify(desc, base_embed=embed)
            await SlashMenuView(interaction, pages).start()

        if self.view.choice == 'Plates and Memories':
            #Arceus Plates
            dracoPlate = self.bag_data['draco_plate']
            dreadPlate = self.bag_data['dread_plate']
            earthPlate = self.bag_data['earth_plate']
            fistPlate = self.bag_data['fist_plate']
            flamePlate = self.bag_data['flame_plate']
            iciclePlate = self.bag_data['icicle_plate']
            ironPlate = self.bag_data['iron_plate']
            splashPlate = self.bag_data['splash_plate']
            skyPlate = self.bag_data['sky_plate']
            pixiePlate = self.bag_data['pixie_plate']
            mindPlate = self.bag_data['mind_plate']
            meadowPlate = self.bag_data['meadow_plate']
            insectPlate = self.bag_data['insect_plate']
            spookyPlate = self.bag_data['spooky_plate']
            stonePlate = self.bag_data['stone_plate']
            toxicPlate = self.bag_data['toxic_plate']
            zapPlate = self.bag_data['zap_plate']
            #Silvally Memories
            bug_memory = self.bag_data['bug_memory']
            dark_memory = self.bag_data['dark_memory']
            dragon_memory = self.bag_data['dragon_memory']
            electric_memory = self.bag_data['electric_memory']
            fairy_memory = self.bag_data['fairy_memory']
            fighting_memory = self.bag_data['fighting_memory']
            fire_memory = self.bag_data['fire_memory']
            flying_memory = self.bag_data['flying_memory']
            ghost_memory = self.bag_data['ghost_memory']
            grass_memory = self.bag_data['grass_memory']
            ground_memory = self.bag_data['ground_memory']
            ice_memory = self.bag_data['ice_memory']
            poison_memory = self.bag_data['poison_memory']
            psychic_memory = self.bag_data['psychic_memory']
            rock_memory = self.bag_data['rock_memory']
            steel_memory = self.bag_data['steel_memory']
            water_memory = self.bag_data['water_memory']

            embed = discord.Embed(
                title=f"Plates and Memories", 
                description=f"Plates are used for Arceus\nMemories are used for Silvally", 
                color=0x0084FD
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:draco_plate:1085322300791996486> **Draco Plate**: {dracoPlate}"
                    f"\n<:dread_plate:1085322267342413874> **Dread Plate**: {dreadPlate}"
                    f"\n<:earth_plate:1085322266201571388> **Earth Plate**: {earthPlate}"
                    f"\n<:fist_plate:1085322264913911958> **Fist Plate**: {fistPlate}"
                    f"\n<:flame_plate:1085322264112803901> **Flame Plate**: {flamePlate}"
                    f"\n<:icicle_plate:1085322263236194404> **Icicle Plate**: {iciclePlate}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                f"\n<:splash_plate:1085322093127807096> **Splash Plate**: {splashPlate}"
                f"\n<:sky_plate:1085322093928906902> **Sky Plate**: {skyPlate}"
                f"\n<:pixie_plate:1085322095237533787> **Pixie Plate**: {pixiePlate}"
                f"\n<:mind_plate:1085322095761829940> **Mind Plate**: {mindPlate}"
                f"\n<:meadow_plate:1085322259817828383> **Meadow Plate**: {meadowPlate}"
                f"\n<:insect_plate:1085322262426689728> **Insect Plate**: {insectPlate}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:spooky_plate:1085322092058251265> **Spooky Plate**: {spookyPlate}"
                    f"\n<:stone_plate:1085322090816749642> **Stone Plate**: {stonePlate}"
                    f"\n<:toxic_plate:1085322090091135027> **Toxic Plate**: {toxicPlate}"
                    f"\n<:zap_plate:1085322088656687225> **Zap Plate**: {zapPlate}"
                    f"\n<:icon_plate:1085322261487173733> **Iron Plate**: {ironPlate}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:dragon_memory:1085589410453667880> **Dragon Memory**: {dragon_memory}"
                    f"\n<:dark_memory:1085589411535786065> **Dark Memory**: {dark_memory}"
                    f"\n<:ground_memory:1085589591861502023> **Ground Memory**: {ground_memory}"
                    f"\n<:fighting_memory:1085589598647881881> **Fighting Memory**: {fighting_memory}"
                    f"\n<:fire_memory:1085589597486067743> **Fire Memory**: {fire_memory}"
                    f"\n<:ice_memory:1085589635977191454> **Ice Memory**: {ice_memory}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:steel_memory:1085589630457479189> **Steel Memory**: {steel_memory}"
                    f"\n<:water_memory:1085589629463445565> **Water Memory**: {water_memory}"
                    f"\n<:fairy_memory:1085589407735746640> **Fairy Memory**: {fairy_memory}"
                    f"\n<:psychic_memory:1085589633125056562> **Psychic Memory**: {psychic_memory}"
                    f"\n<:grass_memory:1085589593723777054> **Grass Memory**: {grass_memory}"
                    f"\n<:bug_memory:1085589412441772164> **Bug Memory**: {bug_memory}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"\n<:ghost_memory:1085589594701058139> **Ghost Memory**: {ghost_memory}"
                    f"\n<:rock_memory:1085589632017760436> **Rock Memory**: {rock_memory}"
                    f"\n<:poison_memory:1085589633972318238> **Poison Memory**: {poison_memory}"
                    f"\n<:electric_memory:1085589409459605534> **Electric Memory**: {electric_memory}"
                ),
                inline=True
            )
            embed.set_footer(
                text=f"{interaction.user.name}'s bag"
            )
            await interaction.response.edit_message(embed=embed)

        if self.view.choice == 'Forms':
            FORM_ITEMS = await interaction.client.db[1].form_items.find({}).to_list(None)
            items = [t["item"] for t in FORM_ITEMS]
            desc = ""
            count = 1
            for idx, item in enumerate(items):
                emoji = get_form_emoji(
                    item_name=item.lower()
                )
                amount = self.bag_data_dict[item]
                if count in [7, 14, 21]: 
                    desc += f"{emoji} **{item.title().replace('_', ' ')}**\n`Amount`: {amount:,}\n\n"
                else:
                    desc += f"{emoji} **{item.title().replace('_', ' ')}**\n`Amount`: {amount:,}\n"
                count += 1

            #footer_text = f"{interaction.user.name}'s Bag"
            embed = discord.Embed(
                title="Form Items!", color=3553600)
            #pages = pagify(desc, base_embed=embed, footer=footer_text)
            pages = pagify(desc, base_embed=embed)
            await SlashMenuView(interaction, pages).start()
        
        if self.view.choice == "Battles":
            BATTLE_ITEMS = await interaction.client.db[1].battle_items.find({}).to_list(None)
            items = [t["item"] for t in BATTLE_ITEMS]
            desc = ""
            count = 1
            for idx, item in enumerate(items):
                emoji = get_battle_emoji(
                    item_name = item.lower()
                )
                amount = self.bag_data_dict[item]
                if count in [7, 14, 21, 28, 35, 42, 49, 56, 63, 70]: 
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`Amount`: {amount:,}\n\n"
                else:
                    desc += f"**{emoji} {item.title().replace('_', ' ')}**\n`Amount`: {amount:,}\n"
                count += 1

            #footer_text = f"{interaction.user.name}'s Bag"
            embed = discord.Embed(
                title="Items for Battles!", color=3553600)
            #pages = pagify(desc, base_embed=embed, footer=footer_text)
            pages = pagify(desc, base_embed=embed)
            await SlashMenuView(interaction, pages).start()

        if self.view.choice == "General":            
            lucky_egg = self.bag_data['lucky_egg']
            soothe_bell = self.bag_data['soothe_bell']
            ability_capsule = self.bag_data['ability_capsule']
            destiny_knot = self.bag_data['destiny_knot']
            ultra_destiny_knot = self.bag_data['ultra_destiny_knot']
            sky_crystal = self.bag_data['sky_crystal']
            light_crystal = self.bag_data['light_crystal']
            abyss_crystal = self.bag_data['abyss_crystal']
            internal_crystal = self.bag_data['internal_crystal']
            energy_crystal = self.bag_data['energy_crystal']
            hp_up = self.bag_data['hp_up']
            protein = self.bag_data['protein']
            calcium = self.bag_data['calcium']
            iron = self.bag_data['iron']
            carbos = self.bag_data['carbos']
            zinc = self.bag_data['zinc']

            embed = discord.Embed(
                title=f"General Items", 
                description=f"Different items for various needs!", 
                color=0x0084FD
            )
            embed.add_field(
                name="General Items",
                value=(
                    f"<:luckyegg:668821570973597716> **Lucky Egg**: {lucky_egg}"
                    f"\n<:soothebell:707992343772659793> **Soothe Bell**: {soothe_bell}"
                    f"\n<:ability_capsule:726906080948518962> **Ability Capsule**: {ability_capsule}"
                    f"\n<:destinyknot:679168705141407764> **Destiny Knot**: {destiny_knot}"
                    f"\n<:destinyknot:679168705141407764> **Ultra Destiny Knot**: {ultra_destiny_knot}"
                )
            )
            embed.add_field(
                name="Crystals",
                value=(
                    f"<:sky:682272338963726443> **Sky Crystal**: {sky_crystal}"
                    f"\n<:light:682272339022577764> **Light Crystal**: {light_crystal}"
                    f"\n<:fire:682272339114721306> **Abyss Crystal**: {abyss_crystal}"
                    f"\n<:internal:682272339072909397> **Internal Crystal**: {internal_crystal}"
                    f"\n<:energy:682272339156795421> **Energy Crystal**: {energy_crystal}"
                )
            )
            embed.add_field(
                name="Vitamins",
                value=(
                    f"<:hp_up:1093288050035003442> **HP Up**: {hp_up}\n"
                    f"<:protein:1093288048462147715> **Protein** {protein}\n"
                    f"<:iron:1093288047577157773> **Iron** {iron}\n"
                    f"<:calcium:1093288046536953977> **Calcium** {calcium}\n"
                    f"<:zinc:1093288045765198004> **Zinc** {zinc}\n"
                    f"<:carbos:1093288043991007302> **Carbos** {carbos}\n"
                )
            )
            embed.set_footer(
                text=f"{interaction.user.name}'s bag"
            )

            await interaction.response.edit_message(embed=embed)

        if self.view.choice == "Berries":
            #Berries
            aguav_berry = self.bag_data['aguav_berry']
            apicot_berry = self.bag_data['apicot_berry']
            aspear_berry = self.bag_data['aspear_berry']
            cheri_berry = self.bag_data['cheri_berry']
            chesto_berry = self.bag_data['chesto_berry']
            figy_berry = self.bag_data['figy_berry']
            ganlon_berry = self.bag_data['ganlon_berry']
            iapapa_berry = self.bag_data['iapapa_berry']
            lansat_berry = self.bag_data['lansat_berry']
            liechi_berry = self.bag_data['liechi_berry']
            lum_berry = self.bag_data['lum_berry']
            mago_berry = self.bag_data['mago_berry']
            micle_berry = self.bag_data['micle_berry']
            pecha_berry = self.bag_data['pecha_berry']
            persim_berry = self.bag_data['persim_berry']
            petaya_berry = self.bag_data['petaya_berry']
            rawst_berry = self.bag_data['rawst_berry']
            salac_berry = self.bag_data['salac_berry']
            sitrus_berry = self.bag_data['sitrus_berry']
            starf_berry = self.bag_data['starf_berry']
            wiki_berry = self.bag_data['wiki_berry']
            #Seeds
            aguav_seed = self.bag_data['aguav_seed']
            apicot_seed = self.bag_data['apicot_seed']
            aspear_seed = self.bag_data['aspear_seed']
            cheri_seed = self.bag_data['cheri_seed']
            chesto_seed = self.bag_data['chesto_seed']
            figy_seed = self.bag_data['figy_seed']
            ganlon_seed = self.bag_data['ganlon_seed']
            iapapa_seed = self.bag_data['iapapa_seed']
            lansat_seed = self.bag_data['lansat_seed']
            liechi_seed = self.bag_data['liechi_seed']
            lum_seed = self.bag_data['lum_seed']
            mago_seed = self.bag_data['mago_seed']
            micle_seed = self.bag_data['micle_seed']
            pecha_seed = self.bag_data['pecha_seed']
            persim_seed = self.bag_data['persim_seed']
            petaya_seed = self.bag_data['petaya_seed']
            rawst_seed = self.bag_data['rawst_seed']
            salac_seed = self.bag_data['salac_seed']
            sitrus_seed = self.bag_data['sitrus_seed']
            starf_seed = self.bag_data['starf_seed']
            wiki_seed = self.bag_data['wiki_seed']

            embed = discord.Embed(
                title=f"Berries and Seeds", 
                description=f"Berries held by Pokemon with different effects\nAlong with Seeds for Farming!", 
                color=0x0084FD
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"<:aguav_berry:1085430968455811112> **Aguav**\n`Berry`: {aguav_berry} - `Seed`: {aguav_seed}"
                    f"\n<:apicot_berry:1085430940798566410> **Apicot**\n`Berry`: {apicot_berry} - `Seed`: {apicot_seed}"
                    f"\n<:aspear_berry:1085430915540471929> **Aspear**\n`Berry`: {aspear_berry} - `Seed`: {aspear_seed}"
                    f"\n<:cheri_berry:1085430875300302909> **Cheri**\n`Berry`: {cheri_berry} - `Seed`: {cheri_seed}"
                    f"\n<:chesto_berry:1085430874268500079> **Chesto**\n`Berry`: {chesto_berry} - `Seed`: {chesto_seed}"
                    f"\n<:figy_berry:1085430966899720223> **Figy**\n`Berry`: {figy_berry} - `Seed`: {figy_seed}"
                    f"\n<:ganlon_berry:1085430940001640509> **Ganlon**\n`Berry`: {ganlon_berry} - `Seed`: {ganlon_seed}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"<:iapapa_berry:1085430969684742215> **Iapapa**\n`Berry`: {iapapa_berry} - `Seed`: {iapapa_seed}"
                    f"\n<:lansat_berry:1085430944338550825> **Lansat**\n`Berry`: {lansat_berry} - `Seed`: {lansat_seed}"
                    f"\n<:liechi_berry:1085430914038894602> **Liechi**\n`Berry`: {liechi_berry} - `Seed`: {liechi_seed}"
                    f"\n<:lum_berry:1085430873266069526> **Lum**\n`Berry`: {lum_berry} - `Seed`: {lum_seed}"
                    f"\n<:mago_berry:1085430943852015677> **Mago**\n`Berry`: {mago_berry} - `Seed`: {mago_seed}"
                    f"\n<:micle_berry:1085430912977739826> **Micle**\n`Berry`: {micle_berry} - `Seed`: {micle_seed}"
                    f"\n<:pecha_berry:1085430872523681872> **Pecha**\n`Berry`: {pecha_berry} - `Seed`: {pecha_seed}"
                ),
                inline=True
            )
            embed.add_field(
                name=f"<:blank:1012504803496177685>",
                value=(
                    f"<:persim_berry:1085430878135660574> **Persim**\n`Berry`: {persim_berry} - `Seed`: {persim_seed}"
                    f"\n<:petaya_berry:1085430911945940992> **Petaya**\n`Berry`: {petaya_berry} - `Seed`: {petaya_seed}"
                    f"\n<:rawst_berry:1085430876407611464> **Rawst**\n`Berry`: {rawst_berry} - `Seed`: {rawst_seed}"
                    f"\n<:salac_berry:1085430910842843217> **Salac**\n`Berry`: {salac_berry} - `Seed`: {salac_seed}"
                    f"\n<:sitrus_berry:1085430942065242112> **Sitrus**\n`Berry`: {sitrus_berry} - `Seed`: {sitrus_seed}"
                    f"\n<:starf_berry:1085430909492273182> **Starf**\n`Berry`: {starf_berry} - `Seed`: {starf_seed}"
                    f"\n<:wiki_berry:1085430943071883304> **Wiki**\n`Berry`: {wiki_berry} - `Seed`: {wiki_seed}"
                ),
                inline=True
            )
            embed.set_footer(
                text=f"{interaction.user.name}'s bag"
            )

            await interaction.response.edit_message(embed=embed)

class BagView(discord.ui.View):
    """View that helps character commands""" 
    def __init__(self, ctx, bag_data):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.bag_data = bag_data
        self.event = asyncio.Event()
        self.message = ""
        self.add_item(DropdownSelect(bag_data))

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
        #Start creating base embed    
        embed = discord.Embed(
            title=f"{self.ctx.author.name}'s Bag",
            description=f"Choose an option from the dropdown menu below!",
            color=0x4F2683
        )
        embed.set_image(url="https://dyleee.github.io/mewbot-images/bag_image.png")
        self.message = await self.ctx.send(embed=embed, view=self)
        await self.event.wait()
    
class Bag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def bag(self, ctx):
        """
        Bag command
        """
        pass

    @bag.command()
    async def view(self, ctx):
        """View new bag system"""
        async with ctx.bot.db[0].acquire() as pconn:
            bag_data = await pconn.fetchrow(
                "SELECT * FROM bag WHERE u_id = $1",
                ctx.author.id
            )

        if bag_data is None:
            await ctx.send("Have you converted to the new bag system?\nUse `/bag convert` if you haven't!")
            return

        await BagView(
            ctx, 
            bag_data
        ).wait()

    @bag.command()
    async def convert(self, ctx):
        #if ctx.author.id != 334155028170407949:
            #await ctx.send("Not available yet")
            #return
        """Move data from item/inventory json to new bag tables"""
        #Alright pull the players original inventory
        async with ctx.bot.db[0].acquire() as conn:
            dets = await conn.fetchrow(
                "SELECT bag_convert, items::json, inventory::json FROM users WHERE u_id = $1",
                  ctx.author.id
            )
            bound_dets = await conn.fetchval(
                "SELECT inventory::json FROM users WHERE u_id = $1",
                ctx.author.id
            )
            if dets is None:
                await ctx.send(f"You have not Started!\nStart with `/start` first!")
                return
            
            if dets['bag_convert'] == True:
                await ctx.send("Sorry, you've already converted your bag!")
                return
            
            #Mark conversion complete so it isn't abused
            await conn.execute(
                "UPDATE users SET bag_convert = True WHERE u_id = $1",
                  ctx.author.id
            )

        dets = dets['items']
        msg = ""
        amount_transferred = 0
        for item in dets:
            if dets[item] > 0:
                try:
                    #Accounts for mistype in some user's bag
                    if item == 'poison-bard':
                        item = 'poison_barb'
                    if item == 'sunstone':
                        item = 'sun_stone'
                    if "-rod" not in item:
                        await self.bot.commondb.add_bag_item(
                            ctx.author.id,
                            item.replace("-", "_").lower(),
                            dets[item]
                        )
                        amount_transferred += dets[item]
                except:
                    if item not in ('poison_barb', 'sun_stone', 'ultra_destiny_knot'):
                        msg += f"{item}\n"
        await ctx.send(f"Normal bag completed, starting on account bound items <@{ctx.author.id}>")
        for item in bound_dets:
            if bound_dets[item] > 0:
                try:
                    amount_gained = bound_dets[item]
                    item = item.replace("-", "_").lower()
                    item = item.replace("_", " ").lower()
                    item = item.replace(" ", "_").lower()

                    #Accounts for mistype in some user's bag
                    await self.bot.commondb.add_bag_item(
                        ctx.author.id,
                        item,
                        amount_gained,
                        True
                    )
                    
                    amount_transferred += amount_gained
                except:
                    if item not in ('poison_barb', 'sun_stone', 'ultra_destiny_knot'):
                        msg += f"{item}\n"

        await ctx.send(f"Transferred items - {amount_transferred} items sent.\nItems below were not added to be added to bag table. Please report this in Mewbot Official.\n{msg}")

    @bag.command()
    @commands.cooldown(2, 30, commands.BucketType.default)
    async def old(self, ctx):
        """See the old bag embed"""
        async with ctx.bot.db[0].acquire() as conn:
            dets = await conn.fetchval(
                "SELECT items::json FROM users WHERE u_id = $1", ctx.author.id
            )
        if dets is None:
            await ctx.send(f"You have not Started!\nStart with `/start` first!")
            return
        desc = ""
        for item in dets:
            if dets[item] > 0:
                desc += f"{item.replace('-', ' ').capitalize()} : {dets[item]}x\n"
        if not desc:
            e = discord.Embed(
                title="Your Current Bag", 
                description="Empty :(",
                color=0xFFB6C1, 
            )
            await ctx.send(embed=e)
            return

        embed = discord.Embed(
            title="Your Current Bag", 
            color=0xFFB6C1
        )
        pages = pagify(desc, per_page=20, base_embed=embed)
        await MenuView(ctx, pages).start()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bag(bot))