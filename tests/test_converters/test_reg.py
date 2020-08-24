from hikari import Snowflake

from Yami.converters.reg import resolve_id_from_arg, USER_MENTION_REGEX


def test_resolve_id_from_user_arg():
    assert resolve_id_from_arg(
        "<@!292577213226811392>", USER_MENTION_REGEX
    ) == Snowflake(292577213226811392)
