from lightbulb import Context


def name(context: Context):
    return (
        context.member.nickname or context.author.username
        if context.member
        else context.author.username
    )
