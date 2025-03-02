import discord
import random
import traceback
import os
from mewutils.misc import OLD_SKIN_LIST, reverse_id
from mewcogs.pokemon_list import natlist


class MewMisc:
    CREDITS_EMOJI = "<:mewcoin:1010959258638094386>"
    REDEEMS_EMOJI = "<:redeem:1037942226132668417>"

    def __init__(self, bot):
        self.bot = bot
        self.OLD_SKINS = []
        self.ALL_GLEAMS = []
        self.app_emojis = []
        self.emotes = {
            "CREDITS": "<:mewcoin:1010959258638094386>",
            "REDEEMS": "<:redeem:1037942226132668417>",
            "COMMON_CHEST": "<:common_chest:1311626467360378970>",
            "RARE_CHEST": "<:rare_chest:1311626539917512714>",
            "MYTHIC_CHEST": "<:mythic_chest:1311626611220676680>",
            "LEGEND_CHEST": "<:legend_chest:1311626665239117894>",
            "GEMS": "<a:radiantgem:774866137472827432>",
            "GLEAM": "<:gleam:1010559151472115772>",
            "SHINY": ":star2:",
            "SHADOW": "<:shadow:1010559067590246410>",
            "ALPHA": "<:alphapoke2:1145814445239574538>",
            "XMAS": "<:xmas:927667765135945798>",
            "VOTE": "<a:votestreak:998338987070603354>",
            # "PAT_CHEST": "<:patreon:1184571762705432679>",
            "VALENTINE": "<:heart:1184895213399982140>",
            "EASTER": "<:easter:1184895215060914277>",

        }
    def get_emoji(self, emote):
        return self.get_emote(emote)
    
    def get_emote(self, emote_name):
        if not emote_name: emote_name = "" 
        self.bot.logger.info("Fetching Emote %s " % emote_name)

        ##
        if 'voucher' in emote_name:
            emote_name = 'custom'
        elif 'xmas' in emote_name:
            emote_name = 'xmas'
        elif 'valentine' in emote_name:
            emote_name = 'valentine'
        elif 'easter' in emote_name:
            emote_name = 'easter'
        elif 'vote' in emote_name:
            emote_name = 'vote'
        ##

        emote = self.emotes.get(emote_name.upper(), None)
        if not emote:
            emote = discord.utils.get(self.app_emojis, name = emote_name.lower())
        return emote or "<:blank:1012504803496177685>"
    
    async def get_all_gleams(self):
        # Get list of pokemon in old skin folders

        # Initialize a list to store the prefixes
        names = []

        directory = f"/home/dyroot/mewbot/shared/duel/sprites/skins/gleam"
        if os.path.exists(directory) and os.path.isdir(directory):
            # Iterate through the files in the directory
            for item in os.listdir(directory):
                # Check if the file ends with '.png'
                if item.endswith(".png"):
                    # Extract the first 3 letters of the file name (without extension)
                    prefix = item[:3]
                    # Remove letters & shit
                    prefix = "".join(c for c in prefix if c.isdigit())
                    names.append((await reverse_id(int(prefix), self.bot), 'gleam')[0])

        self.ALL_GLEAMS = names
        return
    async def refresh_app_emotes(self):
        self.app_emojis = await self.bot.fetch_application_emojis()

    async def get_old_skins(self):
        # Get list of pokemon in old skin folders

        # Initialize a list to store the prefixes
        names = []
        await self.get_all_gleams()

        for skin in OLD_SKIN_LIST:
            directory = f"/home/dyroot/mewbot/shared/duel/sprites/skins/{skin}"
            if os.path.exists(directory) and os.path.isdir(directory):
                # Iterate through the files in the directory
                for item in os.listdir(directory):
                    # Check if the file ends with '.png'
                    if item.endswith(".png"):
                        # Extract the first 3 letters of the file name (without extension)
                        prefix = item[:3]
                        # Remove letters & shit
                        prefix = "".join(c for c in prefix if c.isdigit())
                        names.append((await reverse_id(int(prefix), self.bot), skin))

        self.OLD_SKINS = names
        return

    def get_vat_price(self, price: int):
        return price
        return price + round(price * (7 / 100))

    def get_txn_surcharge(self, amount: int):
        tax_charge = round(amount * (0.5 / 100))
        if tax_charge > 35000:
            tax_charge = 35000
        total_charge = amount + tax_charge
        return tax_charge, total_charge

    def get_skin_emote(
        self, *, blank="", shiny=False, radiant=False, gleam=False, skin=None
    ):
        """Gets the prefix emoji for a particular pokemon."""
        emoji = blank
        if skin:
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
            elif skin == "alpha":
                emoji = "<:alphapoke2:1145814445239574538>"
            else:
                emoji = "<:skin:1010890087074123777>"
        elif radiant:
            emoji = "<:gleam:1010559151472115772>"
        elif shiny:
            emoji = ":star2:"
        elif blank != "":
            emoji = "<:blank:1012504803496177685>"
        return emoji

    def get_type_emote(self, t):
        t = t.lower()
        types = {
            "normal": "<:normal:763850849952333894>",
            "fighting": "<:fighting:763851021352566784>",
            "flying": "<:flying:763850989408354304>",
            "poison": "<:poison:763850821753503754>",
            "ground": "<:ground:763850907904639007>",
            "rock": "<:rock:763850797939163137>",
            "bug": "<:bug:763851314488672266>",
            "ghost": "<:ghost:763850966105194567>",
            "steel": "<:steel:763850762224271461>",
            "fire": "<:fire:763851153045716992>",
            "water": "<:water:763850734378418257>",
            "grass": "<:grass:763850939483553862>",
            "electric": "<:electric:763851258381074433>",
            "psychic": "<:psychic:763851345593499658>",
            "ice": "<:ice:763850875318829126>",
            "dragon": "<:dragon:764152459751981147>",
            "dark": "<:dark:763851283102695424>",
            "fairy": "<:fairy:763851231931269120>",
        }
        if t not in types:
            return None
        return types[t]

    def get_pokemon_emoji(self, pokemon: str):
        emoji = discord.utils.get(self.bot.emote_server.emojis, name=pokemon.lower())
        return emoji

    def get_egg_emote(self, egg_group):
        egg_group = egg_group.lower()
        egg_groups = {
            "monster": f"{self.get_emote('monster')} `Monster`",
            "bug": f"{self.get_emote('bug')} `Bug`",
            "flying": f"{self.get_emote('flying')} `Flying`",
            "field": f"{self.get_emote('field')} `Field`",
            "fairy": f"{self.get_emote('fairy')} `Fairy`",
            "grass": f"{self.get_emote('grass')} `Grass`",
            "humanlike": f"{self.get_emote('humanlike')} `Humanlike`",
            "mineral": f"{self.get_emote('mineral')} `Mineral`",
            "amorphous": f"{self.get_emote('amorphous')} `Amorphous`",
            "water1": f"{self.get_emote('water1')} `Water1`",
            "water2": f"{self.get_emote('water2')} `Water2`",
            "water3": f"{self.get_emote('water3')} `Water3`",
            "dragon": f"{self.get_emote('dragon')} `Dragon`",
            "ditto": f"{self.get_emote('ditto')} `Ditto`",
            "undiscovered": f"{self.get_emote('undiscovered')} `Undiscovered`",
            "special": f"{self.get_emote('special')} `Special`",
        }
        if egg_group not in egg_groups:
            return None
        return egg_groups[egg_group]

    def get_random_egg_emote(self):
        return random.choice(
            [
                "<:monsteregg:764298668161105961>",
                "<:bugegg:764297919728713729>",
                "<:flyingegg:764297946396098560>",
                "<:fieldegg:764298329675923456>",
                "<:fairyegg:764298417215635477>",
                "<:grassegg:764297886644699197>",
                "<:humanlikeegg:764300101497389066>",
                "<:mineralegg:764298485494710272>",
                "<:amorphousegg:764603483667562587>",
                "<:water1egg:764298234381860904>",
                "<:water2egg:764297822144430100>",
                "<:water3egg:764297852650258452>",
                "<:dragonegg:764298849900298252>",
            ]
        )

    def get_gender_emote(self, gender):
        return (
            "<:male:998336034519654534>"
            if gender == "-m"
            else (
                "<:female:998336077943279747>"
                if gender == "-f"
                else "<:genderless:1029425375589187634>"
            )
        )

    async def log_error(self, ctx, error):
        await ctx.send("`The command encountered an error. Try again in a moment.`")
        cmd = None
        if ctx.command:
            cmd = ctx.command.qualified_name
        ctx.bot.logger.exception(f"\n\nError in command {cmd}\n\n")
        # "404 unknown interaction" from the interaction timing out and becoming invalid before responded to.
        # I don't know how to possibly fix this other than to get a better host, stop spamming logs.
        if isinstance(error, discord.NotFound) and error.code == 10062:
            return

        def paginate(text: str):
            """Paginates arbitrary length text."""
            last = 0
            pages = []
            for curr in range(0, len(text), 1800):
                pages.append(text[last:curr])
                last = curr
            pages.append(text[last : len(text)])
            pages = list(filter(lambda a: a != "", pages))
            return pages

        stack = "".join(traceback.TracebackException.from_exception(error).format())
        pages = paginate(stack)
        for idx, page in enumerate(pages):
            if idx == 0:
                page = (
                    f"Guild ID   {ctx.guild.id}\n"
                    f"Channel ID {ctx.channel.id}\n"
                    f"User ID    {ctx.author.id}\n"
                    f"Path       {ctx.command.qualified_name}\n"
                    f"Args       {ctx.args}\n\n"
                ) + page
            try:
                await ctx.bot.get_partial_messageable(998290948863836160).send(
                    f"```py\n{page}\n```"
                )
            except:
                ctx.bot.logger.exception("Could not send log to channel")
                pass
