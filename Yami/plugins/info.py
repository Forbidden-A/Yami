import platform
from datetime import datetime, timezone

import aiohttp
import hikari
import lightbulb
import multidict
from lightbulb import commands
from lightbulb.context import Context

from Yami.subclasses.plugin import Plugin
from Yami.utils.time import display_time_from_delta


class Info(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.group()
    async def info(self, context: Context):
        return

    @info.command()
    async def bot(self, context: Context):
        """Credits to Yoda#9999"""
        uptime = display_time_from_delta(datetime.now(tz=timezone.utc) - self.bot.start_time)

        embed = hikari.Embed(
            colour=0x3498DB,
            description=(
                "Yami is a discord bot made using [Hikari](https://nekokatt.github.io/hikari/) and [Lightbulb](https://tandemdude.gitlab.io/lightbulb/)\n"
                "[Hikari Discord](https://discord.com/invite/Jx4cNGG)\n"
                "[Hikari Docs](https://nekokatt.github.io/hikari/hikari/index.html)\n"
                "[Hikari Github](https://github.com/nekokatt/hikari)\n"
                "[Hikari PyPi](https://pypi.org/project/hikari/)\n"
                "[Lightbulb Docs](https://tandemdude.gitlab.io/lightbulb/)\n"
                "[Lightbulb Gitlab](https://gitlab.com/tandemdude/lightbulb)\n"
                "[Lightbulb PyPi](https://pypi.org/project/hikari-lightbulb/)\n"
                "[Yami](https://github.com/Forbidden-A/Yami)"
            ),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Hikari Version", value=hikari.__version__, inline=False)
        embed.add_field(name="Aiohttp Version", value=aiohttp.__version__, inline=False)
        embed.add_field(name="MultiDict Version", value=multidict.__version__, inline=False)
        embed.add_field(
            name="Lightbulb Version", value=lightbulb.__version__, inline=False
        )
        embed.add_field(
            name="Python Version", value=platform.python_version(), inline=False
        )
        embed.add_field(name="Uptime", value=uptime, inline=False)
        await context.reply(embed=embed)


def load(bot):
    bot.add_plugin(Info(bot))
