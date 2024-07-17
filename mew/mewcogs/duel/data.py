import discord
import aiohttp
import json
from io import BytesIO
from mewutils.misc import get_file_name
from .buttons import BattlePromptView, PreviewPromptView


async def find(ctx, db, filter):
    return await getattr(ctx.bot.db[1], db).find(filter).to_list(None)


async def find_one(ctx, db, filter):
    return await getattr(ctx.bot.db[1], db).find_one(filter)


async def generate_team_preview(battle):
    e = discord.Embed(
        title="Pokemon Battle accepted! Loading...",
        description="Team Preview",
        color=0xFFB6C1,
    )
    e.set_footer(text="Who Wins!?")
    e.set_image(url="attachment://team_preview.png")

    URL = "http://178.28.0.11:5864/build_team_preview"

    player1_pokemon_info = [
        (pokemon._name.replace(" ", "-"), pokemon.level)
        for pokemon in battle.trainer1.party
    ]
    player1_data = {
        "name": battle.trainer1.name,
        "pokemon_info": [
            (
                "pixel_sprites/"
                + await get_file_name(
                    pokemon[0],
                    battle.ctx.bot,
                ),
                pokemon[1],
            )
            for pokemon in player1_pokemon_info
        ],  # List of (file_path, level)
    }
    player1_data = json.dumps(player1_data)

    player2_pokemon_info = [
        (pokemon._name.replace(" ", "-"), pokemon.level)
        for pokemon in battle.trainer2.party
    ]
    player2_data = {
        "name": battle.trainer2.name,
        "pokemon_info": [
            (
                "pixel_sprites/"
                + await get_file_name(
                    pokemon[0],
                    battle.ctx.bot,
                ),
                pokemon[1],
            )
            for pokemon in player2_pokemon_info
        ],  # List of (file_path, level)
    }
    player2_data = json.dumps(player2_data)
    params = {"player1_data": player1_data, "player2_data": player2_data}
    image = BytesIO()
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, params=params) as resp:
            image.write(await resp.read())
    image.seek(0)
    preview_view = PreviewPromptView(battle)
    await battle.send(
        embed=e, file=discord.File(image, "team_preview.png"), view=preview_view
    )

    return preview_view


async def generate_main_battle_message(battle):
    e = discord.Embed(
        title=f"Battle between {battle.trainer1.name} and {battle.trainer2.name}",
        color=0xFFB6C1,
    )
    if not battle.trainer2.is_human():
        e.set_footer(text=f"Enemy ID: {battle.trainer2.current_pokemon.id} | Use buttons to see move info!")
    else:
        e.set_footer(text="Who Wins!?")

    e.set_image(url="attachment://battle.png")
    URL = "http://178.28.0.11:5864/build"
    p1_data = {
        "substitute": battle.trainer1.current_pokemon.substitute,
        "hp": battle.trainer1.current_pokemon.hp,
        "starting_hp": battle.trainer1.current_pokemon.starting_hp,
    }
    p1_data = json.dumps(p1_data)
    p2_data = {
        "substitute": battle.trainer2.current_pokemon.substitute,
        "hp": battle.trainer2.current_pokemon.hp,
        "starting_hp": battle.trainer2.current_pokemon.starting_hp,
    }
    p2_data = json.dumps(p2_data)

    p1_filename = await get_file_name(
        battle.trainer1.current_pokemon._name.replace(" ", "-"),
        battle.ctx.bot,
        battle.trainer1.current_pokemon.shiny,
        radiant=battle.trainer1.current_pokemon.radiant,
        skin=battle.trainer1.current_pokemon.skin,
    )
    p2_filename = await get_file_name(
        battle.trainer2.current_pokemon._name.replace(" ", "-"),
        battle.ctx.bot,
        battle.trainer2.current_pokemon.shiny,
        radiant=battle.trainer2.current_pokemon.radiant,
        skin=battle.trainer2.current_pokemon.skin,
    )

    params = {
        "poke1_image_url": "sprites/" + p1_filename,
        "poke2_image_url": "sprites/" + p2_filename,
        "poke1": p1_data,
        "poke2": p2_data,
        "background_number": battle.bg_num,
        "weather": battle.weather._weather_type,
        "trick_room": int(battle.trick_room.active()),
    }
    image = BytesIO()
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, params=params) as resp:
            image.write(await resp.read())
    image.seek(0)
    file = discord.File(image, "battle.png")
    try:  # aiohttp 3.7 introduced a bug in dpy which causes this to error when rate limited. This catch just lets the bot continue when that happens.
        battle_view = BattlePromptView(battle)
        await battle.send(embed=e, file=file, view=battle_view)
    except RuntimeError:
        pass
    return battle_view
