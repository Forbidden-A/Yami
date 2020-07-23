from hikari import GuildTextChannel
from lightbulb import plugins, commands, owner_only, guild_only
from lightbulb.context import Context
from lightbulb.converters import text_channel_converter

from Yami import models
from Yami.subclasses.bot import Bot


class Admin(plugins.Plugin):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    # noinspection PyProtectedMember
    @commands.group()
    async def settings(self, context: Context):
        await self.bot._help_impl.send_group_help(
            context=context, group=context.command
        )

    @owner_only()
    @guild_only()
    @settings.command(name="setstarboard", aliases=["ssb"])
    async def set_starboard(self, context: Context, channel: text_channel_converter):
        channel: GuildTextChannel = channel
        guild = await models.Guild.get(id=context.guild_id)
        guild.starboard = channel.id
        await guild.save()
        await context.reply(f"Starboard successfully set to <#{channel.id}>.")

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
