import hikari
from lightbulb import WrappedArg
from lightbulb.converters import _get_or_fetch_guild_channel_from_id
from lightbulb.errors import ConverterFailure

from Yami.converters.reg import CHANNEL_MENTION_REGEX, resolve_id_from_arg


async def guild_channel_converter(arg: WrappedArg) -> hikari.GuildChannel:
    if (channel_id := resolve_id_from_arg(arg.data, CHANNEL_MENTION_REGEX)) is not None:
        if (
            channel := await _get_or_fetch_guild_channel_from_id(arg, channel_id)
        ) is not None and isinstance(channel, hikari.GuildChannel):
            return channel
    raise ConverterFailure("Unable to get guild channel from id")
