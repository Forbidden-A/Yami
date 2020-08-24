import typing
from lightbulb import WrappedArg, commands, plugins
from lightbulb.errors import ConverterFailure


async def command_or_plugin_converter(
    arg: WrappedArg,
) -> typing.Union[commands.Command, plugins.Plugin]:
    try:
        if (command := arg.context.bot.get_command(arg.data)) is not None:
            return command
    except KeyError:
        pass
    try:
        if (plugin := arg.context.bot.get_plugin(arg.data)) is not None:
            return plugin
    except KeyError:
        pass
    raise ConverterFailure(f"Unable to get command nor plugin with name {arg}")
