from hikari import Member
from lightbulb import Context


def ctx_name(context: Context):
    return (
        context.member.nickname or context.author.username
        if context.member
        else context.author.username
    )


def m_name(member: Member):
    return member.nickname or member.username
