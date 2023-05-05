import discord
import random
import traceback
from mewcogs.pokemon_list import natlist


class MewMisc:
    CREDITS_EMOJI = "<:mewcoin:1010959258638094386>"
    REDEEMS_EMOJI = "<:redeem:1037942226132668417>"

    def __init__(self, bot):
        self.bot = bot
        self.emotes = {
            "CREDITS": "<:mewcoin:1010959258638094386>",
            "REDEEMS": "<:redeem:1037942226132668417>",
        }

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

    def get_egg_emote(self, egg_group):
        egg_group = egg_group.lower()
        egg_groups = {
            "monster": "<:monsteregg:764298668161105961> `monster`",
            "bug": "<:bugegg:764297919728713729> `bug`",
            "flying": "<:flyingegg:764297946396098560> `flying`",
            "field": "<:fieldegg:764298329675923456> `field`",
            "fairy": "<:fairyegg:764298417215635477> `fairy`",
            "grass": "<:grassegg:764297886644699197> `grass`",
            "humanlike": "<:humanlikeegg:764300101497389066> `humanlike`",
            "mineral": "<:mineralegg:764298485494710272> `mineral`",
            "amorphous": "<:amorphousegg:764603483667562587> `amorphous`",
            "water1": "<:water1egg:764298234381860904> `water1`",
            "water2": "<:water2egg:764297822144430100> `water2`",
            "water3": "<:water3egg:764297852650258452> `water3`",
            "dragon": "<:dragonegg:764298849900298252> `dragon`",
            "ditto": "`ditto`",
            "undiscovered": "`undiscovered`",
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
