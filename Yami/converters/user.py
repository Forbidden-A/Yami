import hikari
from lightbulb import WrappedArg
from lightbulb.errors import ConverterFailure

from Yami.converters.reg import resolve_id_from_arg, USER_MENTION_REGEX


# noinspection PyShadowingNames
async def user_converter(arg: WrappedArg) -> hikari.User:
    if (user_id := resolve_id_from_arg(arg.data, USER_MENTION_REGEX)) is not None:
        # noinspection PyProtectedMember
        if (user := arg.context.bot.cache.get_user(user_id)) is not None:
            return user
        return await arg.context.bot.rest.fetch_user(user_id)
    else:
        # noinspection PyProtectedMember
        users = tuple(
            filter(
                lambda user: user.username == arg,
                arg.context.bot.cache.get_users_view().values(),
            )
        )
        if users:
            return users[0]
        raise ConverterFailure(f'Unable to get member by username nor id. "{arg}"')
