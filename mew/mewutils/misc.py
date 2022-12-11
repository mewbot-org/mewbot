#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
from typing import Awaitable, Callable, List, Union
import asyncpg
import os
import asyncio
import logging
import socket
import base64
from concurrent import futures
import functools
from PIL import Image as im, ImageOps as imo
import aiohttp
import discord
import sys
from io import BytesIO

STAFFSERVER = int(os.environ["OFFICIAL_SERVER"])

# TODO: figure out how to remove this w/o breaking the entire bot
FORMS = [
    "-bug",
    "-summer",
    "-marine",
    "-b",
    "-elegant",
    "-poison",
    "-average",
    "-altered",
    "-winter",
    "-trash",
    "-incarnate",
    "-baile",
    "-rainy",
    "-steel",
    "-star",
    "-ash",
    "-diamond",
    "-pop-star",
    "-fan",
    "-school",
    "-therian",
    "-pau",
    "-u",
    "-river",
    "-k",
    "-poke-ball",
    "-kabuki",
    "-electric",
    "-heat",
    "-h",
    "-unbound",
    "-q",
    "-chill",
    "-archipelago",
    "-zen",
    "-normal",
    "-mega-y",
    "-n",
    "-resolute",
    "-blade",
    "-speed",
    "-indigo",
    "-dusk",
    "-sky",
    "-west",
    "-sun",
    "-dandy",
    "-solo",
    "-high-plains",
    "-t",
    "-la-reine",
    "-50",
    "-c",
    "-unova-cap",
    "-burn",
    "-mega-x",
    "-monsoon",
    "-primal",
    "-mother",
    "-red-striped",
    "-ground",
    "-super",
    "-yellow",
    "-p",
    "-polar",
    "-i",
    "-cosplay",
    "-ultra",
    "-heart",
    "-snowy",
    "-sensu",
    "-eternal",
    "-douse",
    "-defense",
    "-sunshine",
    "-w",
    "-psychic",
    "-modern",
    "-natural",
    "-tundra",
    "-flying",
    "-pharaoh",
    "-libre",
    "-sunny",
    "-autumn",
    "-10",
    "-orange",
    "-standard",
    "-land",
    "-partner",
    "-dragon",
    "-plant",
    "-pirouette",
    "-y",
    "-v",
    "-male",
    "-hoenn-cap",
    "-l",
    "-violet",
    "-spring",
    "-fighting",
    "-sandstorm",
    "-original-cap",
    "-neutral",
    "-fire",
    "-fairy",
    "-attack",
    "-black",
    "-shock",
    "-shield",
    "-shadow",
    "-grass",
    "-continental",
    "-overcast",
    "-blue-striped",
    "-disguised",
    "-e",
    "-r",
    "-exclamation",
    "-origin",
    "-garden",
    "-j",
    "-blue",
    "-matron",
    "-red-meteor",
    "-small",
    "-rock-star",
    "-belle",
    "-alola-cap",
    "-green",
    "-active",
    "-red",
    "-mow",
    "-icy-snow",
    "-debutante",
    "-east",
    "-midday",
    "-jungle",
    "-s",
    "-frost",
    "-midnight",
    "-rock",
    "-fancy",
    "-busted",
    "-misfit",
    "-ordinary",
    "-x",
    "-water",
    "-phd",
    "-ice",
    "-spiky-eared",
    "-g",
    "-savanna",
    "-d",
    "-original",
    "-ghost",
    "-meadow",
    "-dawn",
    "-question",
    "-pom-pom",
    "-female",
    "-kalos-cap",
    "-confined",
    "-sinnoh-cap",
    "-a",
    "-aria",
    "-dark",
    "-ocean",
    "-wash",
    "-white",
    "-mega",
    "-sandy",
    "-complete",
    "-large",
    "-alola",
    "-galar",
    "-skylarr",
    "-crowned",
    "-flame",
    "-indo",
    "-silversmith",
    "-draxxx",
    "-dylee",
    "-doomed",
    "-darkbritual",
    "-cheese",
    "-sins",
    "-kyp",
    "-djspree",
    "-jordant",
    "-rasp",
    "-nah",
    "-speedy",
    "-neuro",
    "-jamesy",
    "-pepe",
    "-shadow-rider",
    "-ice-rider",
    "-savvy",
    "-zen-galar",
    "-gorging",
    "-souta",
    "-glaceon",
    "-kanna",
    "-snowy",
    "-toe",
    "-earl",
    "-cruithne",
    "-deezy",
]

# https://github.com/Cog-Creators/Red-DiscordBot/blob/febca8ccbb10d4a618a20c5a25df86ca3532acb0/redbot/core/utils/__init__.py#L265
class AsyncIter:
    """Asynchronous iterator yielding items from ``iterable``
    that sleeps for ``delay`` seconds every ``steps`` items.
    Parameters
    ----------
    iterable: Iterable
        The iterable to make async.
    delay: Union[float, int]
        The amount of time in seconds to sleep.
    steps: int
        The number of iterations between sleeps.
    Raises
    ------
    ValueError
        When ``steps`` is lower than 1.
    Examples
    --------
    >>> from redbot.core.utils import AsyncIter
    >>> async for value in AsyncIter(range(3)):
    ...     print(value)
    0
    1
    2
    """

    def __init__(self, iterable, delay=0, steps: int = 1) -> None:
        if steps < 1:
            raise ValueError("Steps must be higher than or equals to 1")
        self._delay = delay
        self._iterator = iter(iterable)
        self._i = 0
        self._steps = steps
        self._map = None

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            item = next(self._iterator)
        except StopIteration:
            raise StopAsyncIteration
        if self._i == self._steps:
            self._i = 0
            await asyncio.sleep(self._delay)
        self._i += 1
        return await maybe_coroutine(self._map, item) if self._map is not None else item

    def __await__(self):
        """Returns a list of the iterable.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> iterator = AsyncIter(range(5))
        >>> await iterator
        [0, 1, 2, 3, 4]
        """
        return self.flatten().__await__()

    async def next(self, default=...):
        """Returns a next entry of the iterable.
        Parameters
        ----------
        default: Optional[Any]
            The value to return if the iterator is exhausted.
        Raises
        ------
        StopAsyncIteration
            When ``default`` is not specified and the iterator has been exhausted.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> iterator = AsyncIter(range(5))
        >>> await iterator.next()
        0
        >>> await iterator.next()
        1
        """
        try:
            value = await self.__anext__()
        except StopAsyncIteration:
            if default is ...:
                raise
            value = default
        return value

    async def flatten(self):
        """Returns a list of the iterable.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> iterator = AsyncIter(range(5))
        >>> await iterator.flatten()
        [0, 1, 2, 3, 4]
        """
        return [item async for item in self]

    def filter(self, function):
        """Filter the iterable with an (optionally async) predicate.
        Parameters
        ----------
        function: Callable[[T], Union[bool, Awaitable[bool]]]
            A function or coroutine function which takes one item of ``iterable``
            as an argument, and returns ``True`` or ``False``.
        Returns
        -------
        AsyncFilter[T]
            An object which can either be awaited to yield a list of the filtered
            items, or can also act as an async iterator to yield items one by one.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> def predicate(value):
        ...     return value <= 5
        >>> iterator = AsyncIter([1, 10, 5, 100])
        >>> async for i in iterator.filter(predicate):
        ...     print(i)
        1
        5
        >>> from redbot.core.utils import AsyncIter
        >>> def predicate(value):
        ...     return value <= 5
        >>> iterator = AsyncIter([1, 10, 5, 100])
        >>> await iterator.filter(predicate)
        [1, 5]
        """
        return async_filter(function, self)

    def enumerate(self, start: int = 0):
        """Async iterable version of `enumerate`.
        Parameters
        ----------
        start: int
            The index to start from. Defaults to 0.
        Returns
        -------
        AsyncIterator[Tuple[int, T]]
            An async iterator of tuples in the form of ``(index, item)``.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> iterator = AsyncIter(['one', 'two', 'three'])
        >>> async for i in iterator.enumerate(start=10):
        ...     print(i)
        (10, 'one')
        (11, 'two')
        (12, 'three')
        """
        return async_enumerate(self, start)

    async def without_duplicates(self):
        """
        Iterates while omitting duplicated entries.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> iterator = AsyncIter([1,2,3,3,4,4,5])
        >>> async for i in iterator.without_duplicates():
        ...     print(i)
        1
        2
        3
        4
        5
        """
        _temp = set()
        async for item in self:
            if item not in _temp:
                yield item
                _temp.add(item)
        del _temp

    async def find(
        self,
        predicate,
        default=None,
    ):
        """Calls ``predicate`` over items in iterable and return first value to match.
        Parameters
        ----------
        predicate: Union[Callable, Coroutine]
            A function that returns a boolean-like result. The predicate provided can be a coroutine.
        default: Optional[Any]
            The value to return if there are no matches.
        Raises
        ------
        TypeError
            When ``predicate`` is not a callable.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> await AsyncIter(range(3)).find(lambda x: x == 1)
        1
        """
        while True:
            try:
                elem = await self.__anext__()
            except StopAsyncIteration:
                return default
            ret = await maybe_coroutine(predicate, elem)
            if ret:
                return elem

    def map(self, func):
        """Set the mapping callable for this instance of `AsyncIter`.
        .. important::
            This should be called after AsyncIter initialization and before any other of its methods.
        Parameters
        ----------
        func: Union[Callable, Coroutine]
            The function to map values to. The function provided can be a coroutine.
        Raises
        ------
        TypeError
            When ``func`` is not a callable.
        Examples
        --------
        >>> from redbot.core.utils import AsyncIter
        >>> async for value in AsyncIter(range(3)).map(bool):
        ...     print(value)
        False
        True
        True
        """

        if not callable(func):
            raise TypeError("Mapping must be a callable.")
        self._map = func
        return


def get_suffix(name):
    for suffix in FORMS:
        if name.endswith(suffix):
            return suffix
    return None


def is_formed(name):
    return any(name.endswith(suffix) for suffix in FORMS)


def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + enc[i] - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


async def get_pokemon_image(name, bot, shiny=None, *, radiant=False, skin=None):
    if isinstance(name, dict):
        name = decode(*list(name.values()))
    return await get_spawn_url(
        await get_file_name(name, bot, shiny, radiant=radiant, skin=skin)
    )


async def get_file_name(name, bot, shiny=False, *, radiant=False, skin=None):
    name = name.lower()
    identifier = await bot.db[1].forms.find_one({"identifier": name})
    if not identifier:
        # I have NO idea how this can be handled yet, raising for now to avoid breaking other code while still making errors clearer.
        raise ValueError(
            f"Invalid name ({name}) passed to mew/utils/misc.py get_file_name."
        )

    # suffix = get_suffix(name)
    suffix = identifier["form_identifier"]

    if suffix and name.endswith(suffix):
        form_id = int(identifier["form_order"] - 1)
        form_name = name[: -(len(suffix) + 1)]
        pokemon_identifier = await bot.db[1].forms.find_one({"identifier": form_name})
        if not pokemon_identifier:
            # I have NO idea how this can be handled yet, raising for now to avoid breaking other code while still making errors clearer.
            raise ValueError(
                f"Invalid name ({name}) passed to mew/utils/misc.py get_file_name."
            )
        pokemon_id = pokemon_identifier["pokemon_id"]
    else:
        pokemon_id = identifier["pokemon_id"]
        form_id = 0
    filetype = "png"
    if skin is None:
        skin = ""
    else:
        if skin.endswith("_gif"):
            filetype = "gif"
        skin = f"skins/{skin}/"
    is_shiny = "shiny/" if shiny else ""
    new_name = f"{is_shiny}{skin}{pokemon_id}-{form_id}-.{filetype}"
    return new_name


def scale_image(image, width=None, height=None):
    original_image = image
    w, h = original_image.size
    if width and height:
        max_size = (width, height)
    elif width:
        max_size = (width, h)
    elif height:
        max_size = (w, height)
    else:
        # No width or height specified
        raise RuntimeError("Width or height required!")
    original_image.thumbnail(max_size, im.ANTIALIAS)
    return original_image


async def get_spawn_url(pokemon_name):
    # key = Fernet.generate_key()
    # cipher_suite = Fernet(key);
    # cipher_text = cipher_suite.encrypt(pokemon_name.encode())
    # payload = {'cipher_text': cipher_text.decode(), 'key': key.decode()}
    return "https://dyleee.github.io/mewbot-images/sprites/" + pokemon_name


async def get_battle_image(poke1, poke2, bot):
    poke1.name = poke1.name.replace(" ", "-")
    poke2.name = poke2.name.replace(" ", "-")

    base_url = await get_pokemon_image(
        poke1.name, bot, poke1.shiny, radiant=poke1.radiant
    )
    _base_url = await get_pokemon_image(
        poke2.name, bot, poke2.shiny, radiant=poke2.radiant
    )

    async with aiohttp.request("get", base_url) as pBack:

        pBack = await pBack.read()

        s = await run_in_tpe(im.open, BytesIO(pBack))
        s = await run_in_tpe(s.convert, "RGBA")

    async with aiohttp.request("get", _base_url) as pFront:

        pFront = await pFront.read()

        g = await run_in_tpe(im.open, BytesIO(pFront))
        g = await run_in_tpe(g.convert, "RGBA")

    return s, g


def get_emoji(*, blank="", shiny=False, radiant=False, gleam=False, skin=None):
    """Gets the prefix emoji for a particular pokemon."""
    emoji = blank
    if skin is not None:
        skin = skin.lower()
        emoji = ":question:"
        if skin == "staff":
            emoji = "<:staff:867903114841423902>"
        elif skin == "custom":
            emoji = "<:custom:867904645447548929>"
        elif skin == "patreon":
            emoji = "<a:patreon:906307892565672036>"
        elif skin in ("vote", "vote2", "vote3"):
            emoji = "<a:votestreak:998338987070603354>"  # Can Use
        elif skin in ("rad", "rad2", "rad3"):
            emoji = "<a:radiant2:909627287094317097>"
        elif skin == "xmas":
            emoji = "<:xmas:927667765135945798>"
        elif skin == "xmas_special":
            emoji = "<:xmas_special:927668471943282698>"
        elif skin == "tourney":
            emoji = "<:tourney:927669898715471893>"
        elif skin == "shadow":
            emoji = "<:shadow:1010559067590246410>"
        elif skin == "oldrad":
            emoji = "<:radiant:1010558960027308052>"
        elif skin == "radiant":
            emoji = "<:radiant:1010558960027308052>"
        elif skin == "gleam":
            emoji = "<:gleam:1010559151472115772>"
        else:
            emoji = "<:skin:1010890087074123777>"
    elif radiant:
        emoji = "<:gleam:1010559151472115772>"
    elif shiny:
        emoji = ":star2:"
    return emoji


async def run_in_tpe(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    partial = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, partial)


def pagify(text: str, *, per_page: int = 15, sep: str = "\n", base_embed=None):
    """
    Splits the provided `text` into pages.

    The text is split by `sep`, then `per_page` are recombined into a "page".
    This does not validate page length restrictions.

    If `base_embed` is provided, it will be used as a template. The description
    field will be filled with the pages, and the footer will show the page number.
    Returns List[str], or List[discord.Embed] if `base_embed` is provided.
    """
    page = ""
    pages = []
    raw = text.strip().split(sep)
    total_pages = ((len(raw) - 1) // per_page) + 1
    for idx, part in enumerate(raw):
        page += part + sep
        if idx % per_page == per_page - 1 or idx == len(raw) - 1:
            # Strip out the last sep
            page = page[: -len(sep)]
            if base_embed is not None:
                embed = base_embed.copy()
                embed.description = page
                embed.set_footer(text=f"Page {(idx // per_page) + 1}/{total_pages}")
                pages.append(embed)
            else:
                pages.append(page)
            page = ""
    return pages


class FirstPageButton(discord.ui.Button):
    """Button which moves the menu to the first page."""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
        )

    async def callback(self, interaction):
        self.view.page = 0
        await self.view.handle_page(interaction.response.edit_message)


class LeftPageButton(discord.ui.Button):
    """Button which moves the menu back a page."""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary, emoji="\N{BLACK LEFT-POINTING TRIANGLE}"
        )

    async def callback(self, interaction):
        self.view.page -= 1
        self.view.page %= len(self.view.pages)
        await self.view.handle_page(interaction.response.edit_message)


class CloseMenuButton(discord.ui.Button):
    """Button which closes the menu, deleting the menu message."""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger, emoji="\N{HEAVY MULTIPLICATION X}"
        )

    async def callback(self, interaction):
        await interaction.response.defer()
        if interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            try:
                await interaction.delete_original_response()
            except:
                pass
        self.view.stop()


class RightPageButton(discord.ui.Button):
    """Button which moves the menu forward a page."""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary, emoji="\N{BLACK RIGHT-POINTING TRIANGLE}"
        )

    async def callback(self, interaction):
        self.view.page += 1
        self.view.page %= len(self.view.pages)
        await self.view.handle_page(interaction.response.edit_message)


class LastPageButton(discord.ui.Button):
    """Button which moves the menu to the last page."""

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
        )

    async def callback(self, interaction):
        self.view.page = len(self.view.pages) - 1
        await self.view.handle_page(interaction.response.edit_message)


class MenuView(discord.ui.View):
    """View that creates a menu using the List[str] or List[embed] provided."""

    def __init__(
        self, ctx: "commands.Context", pages: "List[Union[str, discord.Embed]]"
    ):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.pages = pages
        self.page = 0
        if len(self.pages) > 1:
            self.add_item(FirstPageButton())
            self.add_item(LeftPageButton())
        self.add_item(CloseMenuButton())
        if len(self.pages) > 1:
            self.add_item(RightPageButton())
            self.add_item(LastPageButton())

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

    async def on_error(self, error, item, interaction):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def handle_page(self, edit_func):
        if isinstance(self.pages[0], discord.Embed):
            await edit_func(embed=self.pages[self.page])
        else:
            await edit_func(content=self.pages[self.page])

    async def start(self):
        if len(self.pages) < 1:
            raise RuntimeError("Must provide at least 1 page.")
        if isinstance(self.pages[0], discord.Embed):
            self.message = await self.ctx.send(embed=self.pages[0], view=self)
        else:
            self.message = await self.ctx.send(self.pages[0], view=self)
        return self.message


class ConfirmView(discord.ui.View):
    """View to confirm or cancel an action."""

    def __init__(
        self,
        ctx: "commands.Context",
        confirm_content: str,
        allowed_interactors: List[int] = None,
        on_confirm: Callable[[], Awaitable] = None,
        on_timeout: Callable[[], Awaitable] = None,
        interaction=None,
    ):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.cancelled = False
        self.confirm = False
        self.event = asyncio.Event()
        self.confirm_content = confirm_content
        # if this is true, then all people in allowed_interactors must interact with the view
        self.allowed_interactors = allowed_interactors or []
        # on_confirm is called when the view is confirmed and allowed_interactors contains one value
        self.on_confirm = on_confirm
        self._on_timeout = on_timeout
        self.interaction = interaction
        self.interacted = []

    @discord.ui.button(style=discord.ButtonStyle.green, label="Confirm")
    async def confirm(self, interaction, button):
        if len(self.allowed_interactors) > 1:
            if os.environ.get("DEBUG_MSGS"):
                await interaction.response.send_message(
                    content=f"Confirmed your intent, waiting for other player {self.interacted=}",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    content="Confirmed your intent, waiting for other player(s)",
                    ephemeral=True,
                )
        self.confirm = True
        self.event.set()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny")
    async def cancel(self, interaction, button):
        await interaction.response.defer()
        self.cancelled = True
        self.event.set()

    async def interaction_check(self, interaction):
        if (
            self.allowed_interactors
            and interaction.user.id not in self.allowed_interactors
        ):
            if os.environ.get("DEBUG_MSGS"):
                await interaction.response.send_message(
                    content=f"You are not allowed to interact with this button as you are not in {self.allowed_interactors=}.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    content="You are not allowed to interact with this button as you are not in allowed_interactors.",
                    ephemeral=True,
                )
            return False
        elif not self.allowed_interactors and interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content="You are not allowed to interact with this button.",
                ephemeral=True,
            )
            return False

        if len(self.allowed_interactors) == len(self.interacted):
            self.event.set()  # IDK why this is needed, but it is
            return True

        if interaction.user.id in self.interacted:
            await interaction.response.send_message(
                content="You have already interacted with this button.", ephemeral=True
            )
            return False

        self.interacted.append(interaction.user.id)

        if self.allowed_interactors and self.on_confirm:
            await self.on_confirm(interaction, self.message)

        return True

    async def on_timeout(self):
        try:
            await self.message.edit(view=None)
        except discord.NotFound:
            pass

        if self._on_timeout:
            await self._on_timeout(self.ctx, self.message)

        self.event.set()

    async def on_error(self, error, item, interaction):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def wait(self):
        """Returns True if the action was confirmed, False otherwise."""
        if self.interaction:
            self.message = await self.interaction.followup.send(
                self.confirm_content, view=self
            )
        else:
            self.message = await self.ctx.send(self.confirm_content, view=self)
        await self.event.wait()

        if self.cancelled:
            await self.message.edit(view=None)
            return False

        if self.allowed_interactors and len(self.interacted) != len(
            self.allowed_interactors
        ):
            self.event.clear()
            await self.event.wait()

        await self.message.edit(view=None)

        if self.cancelled:
            return False

        return self.confirm


class ListSelect(discord.ui.Select):
    """Drop down selection."""

    def __init__(self, options: list):
        super().__init__(options=[discord.SelectOption(label=x) for x in options])

    async def callback(self, interaction):
        self.view.choice = interaction.data["values"][0]
        self.view.event.set()


class ListSelectView(discord.ui.View):
    """View to convert a list into a drop down selection."""

    def __init__(self, ctx, confirm_content: str, options: list):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.choice = None
        self.event = asyncio.Event()
        self.confirm_content = confirm_content
        self.add_item(ListSelect(options))

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

    async def on_error(self, error, item, interaction):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    async def wait(self):
        """Returns the user's choice, or None if they did not choose in time."""
        self.message = await self.ctx.send(self.confirm_content, view=self)
        await self.event.wait()
        return self.choice


class EnableCommandsView(discord.ui.View):
    """View added to commands in disabled channels that allows those with perms to re-enable commands easily."""

    def __init__(self, ctx: "commands.Context"):
        super().__init__(timeout=60)
        self.ctx = ctx

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content="You are not allowed to interact with this button.",
                ephemeral=True,
            )
            return False
        return True

    async def on_error(self, error, item, interaction):
        await self.ctx.bot.misc.log_error(self.ctx, error)

    @discord.ui.button(label="Re-enable commands", style=discord.ButtonStyle.secondary)
    async def reenable(self, interaction, button):
        current_setting = await self.ctx.bot.mongo_find(
            "guilds", {"id": self.ctx.guild.id}
        )
        # I'm not checking current_setting, since it shouldn't be possible to *not* have settings and get this view
        disabled = set(current_setting["disabled_channels"])
        if self.ctx.channel.id not in disabled:
            await interaction.response.send_message(
                content="Commands have already been re-enabled."
            )
            return
        disabled.remove(self.ctx.channel.id)
        await self.ctx.bot.mongo_update(
            "guilds",
            {"id": self.ctx.guild.id},
            {"disabled_channels": list(disabled)},
        )
        await interaction.response.send_message(
            content=f"Successfully enabled commands in {self.ctx.channel}."
        )
        await self.ctx.bot.load_bans()


def poke_spawn_check(inputted_name: str, pokemon: str) -> bool:
    """Checks that a pokemon name is correct or not"""
    # Add additional valid names to support variations in naming
    catch_options = [pokemon.lower()]

    if pokemon == "mr-mime":
        catch_options.append("mr.-mime")
    elif pokemon == "mime-jr":
        catch_options.append("mime-jr.")
    elif pokemon.endswith("-alola"):
        catch_options.append("alola-" + pokemon[:-6])
        catch_options.append("alolan-" + pokemon[:-6])
    elif pokemon.endswith("-galar"):
        catch_options.append("galar-" + pokemon[:-6])
        catch_options.append("galarian-" + pokemon[:-6])
    elif pokemon.endswith("-hisui"):
        catch_options.append("hisui-" + pokemon[:-6])
        catch_options.append("hisuian-" + pokemon[:-6])
    elif pokemon.endswith("-paldea"):
        catch_options.append("paldea-" + pokemon[:-7])
        catch_options.append("paldean-" + pokemon[:-7])

    if inputted_name.lower().replace(" ", "-") not in catch_options:
        return False
    return True
