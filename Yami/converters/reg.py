import re
import typing

import hikari

USER_MENTION_REGEX: typing.Final[typing.Pattern] = re.compile(r"<@!?(\d+)>")
CHANNEL_MENTION_REGEX: typing.Final[typing.Pattern] = re.compile(r"<#(\d+)>")
ROLE_MENTION_REGEX: typing.Final[typing.Pattern] = re.compile(r"<@&(\d+)>")


def resolve_id_from_arg(
    arg_string: str, regex: typing.Pattern
) -> typing.Optional[hikari.Snowflake]:
    if match := regex.match(arg_string):
        arg_string = match.group(1)
    try:
        return hikari.Snowflake(arg_string)
    except ValueError:
        return None
