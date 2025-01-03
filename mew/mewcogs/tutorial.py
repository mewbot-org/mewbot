import discord

from discord.ext import commands

from mewutils.misc import MenuView


class Tutorial(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        texts = [
            {
                "title" : "Mewbot tutorial",
                "description" : """
                **This tutorial aims to explain the basics of Mewbot.**
                As a new user, you might be confused by the multitude of commands in Mewbot. This guide serves to explain the most fundamental features of mewbot.
                **Table of Contents:**
                
                    - Page 1 - **Catching Pokemon**\n
                    - Page 2 - **Managing your Pokemon**\n
                    - Page 3 - **Dueling with your Pokemon**\n
                    - Page 4 - **Trading your Pokemon**\n
                    - Page 5 - **Breeding your Pokemon**\n
                    - Page 6 - **Selling your Pokemon**\n
                    - Page 7 - **Filtering your Pokemon**\n
                    - Page 8 - **Nicknames and Tags**\n
                    - Page 9 - **Manage your inventory**\n
                    - Page 10 - **Credits and Redeems**\n
                    - Page 11 - **Other miscellaneous activities**\n
                    - Page 12 - **Setting up Mewbot in your server**\n
                Those are the basics of MewBot!
                """,
                "embed_image": ""
            },
            {
                "title" : "Catching pokemon",
                "description": """
                In Mewbot, to catch a Pokemon, you just have to mention it (or ping it) and say it's name after it spawns!
                **You can also use the `/catch <pokemon_name>` command !**
                
                Pokemon spawn as you chat, so keep talking to attract more spawns!
                Server owners can disable spawns in specific channels with `/spawns disable`, or make all spawns go to specific channels with `/redirect add`.

                You can also get Pokemon by __redeeming__.
                Redeems are a special currency that allow you get any Pokemon at all, from Ultra Beasts to Dittoes!
                See page 9, or `/redeem` for more.
                """,
                "embed_image": "https://mewbot.xyz/img/catch_img.jpg"
            },
            {
                "title": "Managing your Pokemon",
                "description": """
                `/p` - List the Pokemon you own.
                `/select <Pokemon #>` - Selects the specified Pokemon .
                - This number can be found using `/p`\n
                `/i [Pokemon #]` - View detailed information about a pokemon. If a pokemon number is not provided, defaults to your selected pokemon.
                - Detailed information includes: `Gender, Name, Level, Ability, Experience, Nature, Type, Egg Group, IVs, EVs, Happiness, Moves, and more.`\n
                `/release <Pokemon #>` - Release a pokemon. Released pokemon cannot be reacquired.
                - You can release multiple Pokemon at once, ex. `/release 1 12 24 48`\n
                `/fav add <Pokemon #>` - Mark a pokemon as a favorite to prevent it from being traded or released.\n
                `/fav remove <Pokemon #>` - Unmark a pokemon as a favorite.\n
                `/buy candy <#>` - Purchase rare candies. Each rare candy increases your Pokemon's level by 1.\n
                `/change nature <nature>` - Use a nature capsule to change your Pokemon's nature.\n
                `/add evs <amount> <stat>` - Add EVs to your selected pokemon.
                """,
            },
            {
                "title": "Dueling with your Pokemon",
                "description": """
                You can challenge your friends to a Pokemon battle using the pokemon you have collected on Mewbot!

                **Prepare for a duel**
                `/moveset` - Show a list of moves your selected Pokemon can learn.\n
                `/learn <slot> <move>` - Teaches a move to your selected Pokemon in the slot selected.\n
                - Pokemon have 4 move slots.
                `/moves` - Shows your selected Pokemon's configured moves.\n
                `/party` - View your Pokemon party. Parties are used for 6v6 duels.\n
                `/party add <slot> <Pokemon #>` - Add the specified Pokemon to the slot selected.\n
                `/party remove <slot>` - Removes the Pokemon in the party slot selected.\n
                `/party register <party name>` - Saves your current party to be loaded again later.\n
                `/party list` - Shows all of your saved parties and their names.\n
                `/party load <party name>` Load a registered party, overriding your current party.\n

                **Take part in a duel**
                `/duel single <@user>` - 1v1 duel another user. This will use your selected pokemon.
                `/duel party <@user>` - 6v6 duel another user. This will use your party.
                `/duel npc` - 1v1 duel an NPC with your selected Pokemon. If you defeat them, you will gain some credits as a reward.
                """,
            },
            {
                "title": "Trading your Pokemon",
                "description": """
                `/gift credits <@user> <# credits>` - Gives the mentioned user the specified amount of credits.
                `/gift pokemon <@user> <Pokemon #>` - Gives the mentioned user the specified Pokemon.
                If you want to give items to a player, you can give them a Pokemon holding that item.
                `/trade <@user>` - Sends a trade request to the mentioned user.
                - The other user player must `accept` the trade prompt to begin the trade.
                - In a trade, the bot will present on-screen buttons which can be used to modify the trade.
                - You are able add or remove multiple Pokemon in the prompt from the `add pokemon` button.
                - When both users tap on the `confirm` button, this completes the trade.

                __Redeems can only be traded in the Mewbot Official Server.__
                __Make sure to check the Pokemon and their # to make sure they are trading the right thing!__
                """,
                "embed_image": "https://i.ibb.co/BgSg7fB/image-2024-12-28-144422316.png"
            },
            {
                "title": "Breeding your Pokemon",
                "description": """
                **Requirements For Breeding**
                **1.** Pokemon must share an egg group.
                - Use `/i <Pokemon name>` to see what egg group the Pokemon is in.
                - You can search for your Pokemon based on their egg group and what Pokemon can breed with them.\n
                `/f p egg-group <egg group>` - Find Pokemon in a specified egg group.\n
                `/breedswith <Pokemon #> [filter args]` - Find Pokemon that can breed with the specified Pokemon.
                - Supports adding additional filter arguments. See page 7 for more information.\n
                **2.** Pokemon must be deformed before being able to breed
                - Use `/deform` with a Pokemon selected to deform it.\n
                **3.** You need to have an available Daycare Space.
                - Use `/bal` to see how many Daycare Spaces you have. 
                - Use `/buy daycare <#>` to buy additional spaces.

                **How to Breed**
                `/breed <male Pokemon #> <female Pokemon #>` - Breed two Pokemon. Pokemon must be in the same egg group to breed.
                - ex. `/breed 12 43`
                - Ditto can breed with any gender of Pokemon that is not in the undiscovered egg group (legendary, mythical, baby Pokemon, and another Ditto). 
                - Manaphy is an exception which will produce Phione.

                `/f p cooldown` - View the breeding cooldown on your female Pokemon.
                `/f p name egg` - View your unhatched eggs.
                `/sell egg <Pokemon #>` - Sell an unhatched egg.
                """,
            },
            {
                "title": "Selling your Pokemon",
                "description": f"""
                `/m add <Pokemon #> <# credits>` - Lists your Pokemon on the market for the amount specified.
                - New market listings require you to have at least 15% of the price you want to set in your balance. \n(If you want to enlist a Pokemon of price 200,000 {self.bot.misc.get_emote('MEWCOIN')}, you should have had at least 30,000 {self.bot.misc.get_emote('MEWCOIN')})
                `/buy item market space` - Purchases an additional market space.\n
                `/m remove <Market ID>` - Removes your Pokemon from the market.\n
                `/m i <Market ID>` - View the specified marketed Pokemon's stats and price.\n
                `/m buy <Market ID>` - Purchase the specified Pokemon from the market.\n
                `/f m <filter args>`  - Searches the market for Pokemon.\n
                - Supports adding additional filter arguments. See page 7 for more information.\n
                `/f m owned` - Views the Pokemon you have listed in the market with the market IDs.
                """,
                "embed_image": "https://i.ibb.co/cggPc5N/image-2024-12-28-144554166.png"
            },
            {
                "title": "Filtering your Pokemon",
                "description": """
                `/order <default | ivs | evs | name | level>` - Order your Pokemon according to a set order.
                `/f p <filter args>` - Filter your owned Pokemon.
                `/f m <filter args>` - Filter the market listings.

                **Basic Filter Arguments:**
                `name <names...>`, `evo <names...> `, `nickname <nick>`,
                `type <types...>`, `egg-group <egg groups...>`, `item <items...>`,
                `nature <natures...>`, `tags <tags...>`, `hidden-power <type>`, 
                `skins [skins...]`, `ot [user_id]`,
                `male`, `female`, `genderless`, `starter`, `legend`, `ultra`, `pseudo`,
                `alola`, `galar`, `shiny`, `radiant`, `regular`, `fav`, `cooldown`

                **Advanced Filter Arguments:**
                `level <level>`, `atkiv <iv>`, `defiv <iv>`, `spatkiv <iv>`, `spdefiv <iv>`, `speediv <iv>`, `hpiv <iv>`
                These arguments support `level 50` to specify an exact value or `level > 50` to specify a relative value.

                **Sorting Arguments:**
                `iv [direction]`, `ev [direction]`, `name [direction]`, `level [direction]`
                These arguments can be passed with an optional direction of either `ascending` or `decending` to specify the direction to sort.

                **Market Arguments:**
                `owned`, `id [direction]`, `price [direction or value]`
                The `price` argument can be used either to filter or to sort, depending on how it is used: 
                `price ascending` - Listings, from low price to high price.
                `price < 10000` - Listings that cost less than 10,000 credits.

                **Arguments can be combined using `&`, `|`, and `!`:**
                `/f p name pikachu | male` - Filters for any pokemon that are either pikachus or are male.
                `/f p type fire & type ghost` - Filters for any pokemon that are duel type fire ghost.
                `/f p !type fire` - Filters for any pokemon that are not a fire type.
                `/f p male & iv` - Filters for male pokemon, sorted by iv.
                `/f p egg amorphous & (male | (!evo mimikyu & female))` - Filters for all pokemon in the amorphous egg group, with female pokemon in the mimikyu evolution line excluded.
                """,
                "embed_image": "https://i.ibb.co/HgQ7pHS/image-2024-12-28-144216984.png"
            },
            {
                "title": "Nicknames and Tags",
                "description": """
                You can add a nickname or tag to your Pokemon to help highlight your favorite Pokemon, or add another level of organization to your collection.

                First off, select the Pokemon that needs to be nicknamed - `/select <Pokemon #>`
                Then you can use `/nick <nickname>` to apply a nickname.
                You can search for your Pokemon by using `/f p nick <nickname>`

                `/tags add <tag> <Pokemon #s>` - Add a tag to one or more Pokemon.
                - Tags cannot have a space.
                - You can add multiple Pokemon at once, ex. `/tags add Kermit 1 22 3 44 5`.\n
                `/tags remove <tag> <Pokemon #s>` - Removes a tag from one or more Pokemon.\n
                `/tags list <Pokemon #>` - Show what tags a Pokemon has been assigned.\n
                `/f p tag <tag>` - Filter pokemon that have been given a certain tag.
                """,
            },
            {
                "title": "Manage your inventory",
                "description": """
                The shop is an area where you can spend your credits on various items for your Pokemon.
                `/bag` - Opens up your inventory to show what items you have.
                `/shop` - Shows what stores are available.
                `/shop <shop name>` - Opens the specified store to view items it sells.
                `/buy item <item name>` - Purchases the specified item for your selected Pokemon.
                `/sell item <item name>` - Sell an item from your bag for 65% of its shop value.
                `/equip <item name>` - Gives the specified item to your selected Pokemon. 
                `/unequip` - Removes your Pokemon's held item and returns it to your bag.
                `/drop` - COMPLETELY DELETES the item held by your selected Pokemon.
                """,
            },
            {
                "title": "Credits and Redeems",
                "description": """
                In Mewbot, you have two major currencies, Credits and Redeems.
                `/profile view` - Shows your Credits, Redeems, EV points, Upvote Points and your Fishing Rod.
               
                **Credits**
                Credits are the main currency of Mewbot that you can use to buy most things.
                You can obtain credits by:
                **1.** Upvoting the bot and claiming rewards
                - Use `/vote` for links to upvote Mewbot.
                - Voting gives you upvote points.
                - Use `/claim` when you have 5 upvote points to get some credits.
                **2.** Trading and selling Pokemon
                - See pages 4 and 6 for more information.
                **3.** Dueling NPC trainers
                - See page 11 for more information.
                **4.** Completing missions
                - See page 11 for more information.
                **5.** Opening chests
                - Chests are found randomly from catching Pokemon or fishing. They can also be bought for credits or redeems.
                **6.** Donating to the bot
                - Use `/donate` to obtain a link. You can donate via Patreon or Paypal.
                - Donations through paypal give **1 redeem** and **2000 credits** per $1 USD donated.
                - Patreon rewards can be claimed monthly using `/predeem`.

                **Redeems**
                Redeems are a special currency that can be used to purchase items that credits can't.
                __Redeems cannot be traded!__
                You can obtain redeems by:
                **1.** Upvoting the bot and claiming rewards
                - Use `/vote` for links to upvote Mewbot.
                - Voting gives you upvote points.
                - Use `/claim` when you have 5 upvote points to get some credits.\n
                **2.** Using the redeem market
                - `/buy redeems` - You can buy 25 redeems per day from other players using the Redeem market.\n
                **3.** Opening chests
                - Chests are found randomly from catching Pokemon or fishing. They can also be bought for credits or redeems.\n
                **4.** Donating to the bot
                - Use `/donate` to obtain a link. You can donate via Patreon or Paypal.
                - Donations through paypal give *3 redeem** and **3000 credits** per $1 USD donated.
                - Patreon rewards can be claimed monthly using `/predeem`.
                """,
            },
            {
                "title": "Other miscellaneous activities",
                "description": """
                `/duel npc` - 1v1 duel an NPC with your selected Pokemon. If you defeat them, you will gain some credits as a reward.
                `/fish` - Guess the water Pokemon's name to catch it.
                - You will need a fishing rod by purchasing one from the shop using `/shop rods`.
                """,
            },
            {
                "title": "Setting up Mewbot in your server",
                "description": """
                **Note**: Only the owner of the server and users with the `manage_messages` permission can configure Mewbot in a server.
                `[channel]` Defaults to the channel it is executed in.

                
                **Managing Spawns**
                `/spawns disable [channel]` - Prevents messages in the provided channel from triggering spawns.
                `/spawns enable [channel]` - Allows messages in the provided channel to trigger spawns.
                
                `/redirect add [channel]` - Adds the provided channel to the redirect list.
                `/redirect remove [channel]` - Removes the provided channel from the redirect list.
                `/redirect clear` - Clear all channels from the redirect list.
                If any channels exist on the redirect list, all spawns will be redirected to a random redirect channel instead of being sent in the channel they were triggered from.
                
                `/spawns check` - Lists the channels in your server, and shows which ones are set up to allow spawns.

                
                **Managing Commands**
                `/commands disable [channel]` - Prevents commands from being used in the provided channel.
                `/commands enable [channel]` - Allows commands to be used in the provided channel.
                
                **Note**: Discord provides a permissions system that allows server owners to modify command permissions per role, channel, and member. See [the blog post](https://discord.com/blog/slash-commands-permissions-discord-apps-bots) for more information.

                
                **Other Commands**
                `/spawns small` - Toggle the size of the pokemon image in a spawn message between a large and small version.
                `/auto delete` - Toggle spawn messages getting deleted when the pokemon despawns.
                `/auto pin` - Toggle automatically pinning rare spawns when they are caught.
                `/silence server` - Silence level up messages across the entire server.
                """,
            },
        ]
        self.pages = []
        for text in texts:
            embed = discord.Embed(color=bot.get_random_color())
            embed.title = text['title']
            embed.description = text['description']
            if 'embed_image' in text and text['embed_image']:
                embed.set_image(url=text['embed_image'])
            self.pages.append(embed)

    @commands.hybrid_command()
    async def tutorial(self, ctx):
        """Opens a brief tutorial providing basic information."""
        await MenuView(ctx, self.pages, 360).start()

    @commands.hybrid_command()
    async def help(self, ctx):
        """Opens a brief tutorial providing basic information."""
        await MenuView(ctx, self.pages, 360).start()


async def setup(bot):
    await bot.add_cog(Tutorial(bot))
