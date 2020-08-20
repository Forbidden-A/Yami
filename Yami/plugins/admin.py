from hikari import GuildTextChannel
from lightbulb import commands, guild_only, owner_only
from lightbulb.context import Context
from lightbulb.converters import text_channel_converter

from Yami import models
from Yami.subclasses.bot import Bot
from Yami.subclasses.plugin import Plugin


class Admin(Plugin):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    # noinspection PyProtectedMember
    @commands.group()
    async def settings(self, context: Context):
        await self.bot._help_impl.send_group_help(
            context=context, group=context.command
        )

    @owner_only()
    @guild_only()
    @settings.command(name="starboard", aliases=["sb"])
    async def get_starboard(self, context: Context):
        guild = await models.Guild.get(id=context.guild_id)
        await context.reply(
            f"Starboard is currently set to {f'<#{guild.starboard}>' if guild.starboard else None}."
        )

    @owner_only()
    @guild_only()
    @settings.command(name="setstarboard", aliases=["ssb"])
    async def set_starboard(
        self, context: Context, channel: text_channel_converter = None
    ):
        channel: GuildTextChannel = channel
        guild = await models.Guild.get(id=context.guild_id)
        guild.starboard = channel.id if channel else None
        await guild.save()
        await context.reply(
            f"Starboard successfully set to {f'<#{channel.id}>' if channel else None}."
        )

    @owner_only()
    @guild_only()
    @settings.command(name="stars", aliases=["s"])
    async def get_stars(self, context: Context):
        guild = await models.Guild.get(id=context.guild_id)
        await context.reply(
            f"{guild.stars} is the amount of stars required for messages to be sent in starboard."
        )

    @owner_only()
    @guild_only()
    @settings.command(name="setstars", aliases=["ss"])
    async def set_stars(self, context: Context, stars: int):
        if stars > 20 or stars < 1:
            return await context.reply(
                f"Can't set stars to {stars}, number must be between 20 and 1"
            )
        guild = await models.Guild.get(id=context.guild_id)
        guild.stars = stars
        await guild.save()
        await context.reply(
            f"{stars} star{'s' if stars > 1 else ''} is the new amount of stars required for messages to be sent in starboard."
        )

    @owner_only()
    @guild_only()
    @settings.command(name="setprefix", aliases=["sp"])
    async def set_prefix(self, context: Context, prefix):
        guild = await models.Guild.get(id=context.guild_id)
        guild.prefix = prefix
        await guild.save()
        await context.reply(f"Prefix successfully set to `{prefix}`.")


def load(bot):
    bot.add_plugin(Admin(bot))
