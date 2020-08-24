# noinspection PyShadowingNames

import hikari
from lightbulb import WrappedArg
from lightbulb.errors import ConverterFailure

from Yami.converters.reg import resolve_id_from_arg, USER_MENTION_REGEX


# noinspection PyShadowingNames
async def member_converter(arg: WrappedArg) -> hikari.Member:
    if (user_id := resolve_id_from_arg(arg.data, USER_MENTION_REGEX)) is not None:
        # noinspection PyProtectedMember
        if not arg.context.bot.is_stateless:
            if (
                member := arg.context.bot.cache.get_member(
                    arg.context.guild_id, user_id
                )
            ) is not None:
                return member
        return await arg.context.bot.rest.fetch_member(arg.context.guild_id, user_id)
    else:
        # noinspection PyProtectedMember
        if arg.context.bot.is_stateless:
            raise ConverterFailure(
                "Unable to get member by nick/username as cache is disabled."
            )
        members = tuple(
            filter(
                lambda member: member.username == arg or member.nickname == arg,
                arg.context.bot.cache.get_members_view_for_guild(
                    arg.context.guild_id
                ).values(),
            )
        )
        if members:
            return members[0]
        raise ConverterFailure(f'Unable to get member by nick/username nor id. "{arg}"')
