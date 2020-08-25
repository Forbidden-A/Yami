from hikari import Snowflake

from Yami.converters.reg import (
    resolve_id_from_arg,
    USER_MENTION_REGEX,
    CHANNEL_MENTION_REGEX,
    ROLE_MENTION_REGEX,
)


def test_resolve_id_from_user_arg():
    assert resolve_id_from_arg(
        "<@!292577213226811392>", USER_MENTION_REGEX
    ) == Snowflake(292577213226811392)
    assert resolve_id_from_arg(
        "<@292577213226811392>", USER_MENTION_REGEX
    ) == Snowflake(292577213226811392)
    assert resolve_id_from_arg("292577213226811392", USER_MENTION_REGEX) == Snowflake(
        292577213226811392
    )


def test_resolve_id_from_channel_arg():
    assert resolve_id_from_arg(
        "<#397823614092574721>", CHANNEL_MENTION_REGEX
    ) == Snowflake(397823614092574721)
    assert resolve_id_from_arg(
        "397823614092574721", CHANNEL_MENTION_REGEX
    ) == Snowflake(397823614092574721)


def test_resolve_id_from_role_arg():
    assert resolve_id_from_arg(
        "<@&265858419049758722>", ROLE_MENTION_REGEX
    ) == Snowflake(265858419049758722)
    assert resolve_id_from_arg("265858419049758722", ROLE_MENTION_REGEX) == Snowflake(
        265858419049758722
    )


def test_resolve_id_from_faulty_arg():
    assert (
        resolve_id_from_arg("Hello, this is some random text.", USER_MENTION_REGEX)
        is None
    )
