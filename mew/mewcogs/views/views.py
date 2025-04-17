import discord

# --- The View class to handle buttons and state ---
class PokemonShopView(discord.ui.View):
    def __init__(self, pokemon_data: dict, initial_index: int = 0, *, timeout: float | None = 180.0, cog_instance):
        super().__init__(timeout=timeout)
        self.pokemon_data = pokemon_data
        self.pokemon_list = list(self.pokemon_data.keys())
        self.current_index = initial_index
        self.message: discord.Message | None = None # To store the message this view is attached to
        self.cog = cog_instance # Reference to the Cog instance for session access

        # Initialize button states
        self._update_buttons()

    async def _create_embed(self) -> discord.Embed:
        """Creates the embed for the current Pokemon."""
        if not self.pokemon_list:
            return discord.Embed(title="Shop Empty", description="No Pokémon available.", color=discord.Color.orange())

        current_pokemon = self.pokemon_list[self.current_index]
        embed = discord.Embed(
            title=f"Pokémon Shop: {current_pokemon.capitalize()}",
            description=f"Check out this awesome Pokémon!\nIt costs {self.pokemon_data[current_pokemon].get('price')} {self.cog.bot.misc.get_emote('easter')}!",
            color=discord.Color.blue() # Or customize color
        )

        # Fetch image using the shared session from the cog
        image_url = self.pokemon_data[current_pokemon].get("image_url")

        if image_url:
            embed.set_image(url=image_url)
        else:
            embed.description = f"Could not load image for {current_pokemon.capitalize()}. Maybe try again later?"
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/188/188918.png") # Pldef aceholder Pokeball

        embed.set_footer(text=f"Item {self.current_index + 1} of {len(self.pokemon_list)}")
        return embed

    def _update_buttons(self):
        """Enable/disable Previous/Next buttons based on index."""
        if not self.pokemon_list or len(self.pokemon_list) <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True
        else:
            # Only disable if wrapping is not desired (simple linear navigation)
            # self.previous_button.disabled = self.current_index == 0
            # self.next_button.disabled = self.current_index == len(self.pokemon_list) - 1
            # Keep enabled for cycling:
            self.previous_button.disabled = False
            self.next_button.disabled = False

    async def update_message(self, interaction: discord.Interaction):
        """Edits the original message with the new embed and updated buttons."""
        self._update_buttons()
        embed = await self._create_embed()
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.HTTPException as e:
            print(f"Failed to edit message: {e}")
            # Maybe the interaction token expired, or message was deleted.
            # You could try fetching the message via self.message.edit() but it might also fail.


    # --- Buttons ---
    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary, custom_id="shop_prev")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pokemon_list:
            await interaction.response.send_message("Shop is empty!", ephemeral=True)
            return

        # Cycle backwards
        self.current_index = (self.current_index - 1 + len(self.pokemon_list)) % len(self.pokemon_list)
        await self.update_message(interaction)

    @discord.ui.button(label="Buy Now", style=discord.ButtonStyle.success, custom_id="shop_buy")
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pokemon_list:
            await interaction.response.send_message("Shop is empty!", ephemeral=True)
            return

        current_pokemon = self.pokemon_list[self.current_index]
        price = self.pokemon_data[current_pokemon].get("price")
        
        try:
            async with self.cog.bot.db[0].acquire() as pconn:
                await pconn.fetchval("UPDATE events_new SET easter_eggs = easter_eggs - $1 WHERE u_id = $2", price, interaction.user.id)
        except Exception as e:
            print(f"Failed to deduct Easter Eggs: {e}")
            return
        # - Adding the pokemon to user's inventory (database interaction)
        await self.cog.bot.commondb.create_poke(
            self.cog.bot,
            interaction.user.id,
            current_pokemon.capitalize(),
            skin="easter2025",
        )
        # - Sending a confirmation message
        await interaction.response.send_message(f"You purchased a {self.cog.bot.misc.get_emote('easter')} {current_pokemon.capitalize()}!", ephemeral=True)
        # Example: Disable buy button after purchase? Or remove item from shop?
        button.disabled = True
        await interaction.edit_original_response(view=self)
        # Or maybe stop the view entirely?
        # self.stop()

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.secondary, custom_id="shop_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pokemon_list:
            await interaction.response.send_message("Shop is empty!", ephemeral=True)
            return

        # Cycle forwards
        self.current_index = (self.current_index + 1) % len(self.pokemon_list)
        await self.update_message(interaction)


    async def on_timeout(self):
        """Called when the view times out."""
        if self.message:
            try:
                # Try to get a fresh version of the message
                message = await self.message.channel.fetch_message(self.message.id)
                # Disable all buttons by removing the view
                await message.edit(view=None)
                # Or disable buttons individually if you prefer:
                # for item in self.children:
                #     item.disabled = True
                # await message.edit(view=self)
            except discord.NotFound:
                print("Shop message not found on timeout (likely deleted).")
            except discord.Forbidden:
                print("Bot lacks permissions to edit the message on timeout.")
            except discord.HTTPException as e:
                 print(f"Failed to edit message on timeout: {e}")
        self.stop() # Ensure the view stops listening

