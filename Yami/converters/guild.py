import hikari
from lightbulb import WrappedArg


async def guild_converter(arg: WrappedArg):
    if not arg.isdigit():
        raise ValueError(f"Invalid guild id: {arg!r}")
    snowflake = hikari.Snowflake(arg)
    return arg.context.bot.cache.get_available_guild(
        snowflake
    ) or await arg.context.bot.rest.fetch_guild(snowflake)
