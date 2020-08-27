import random
import typing
from datetime import datetime, timezone

import hikari
from lightbulb import (
    Command,
    Context,
    Group,
    HelpCommand,
    filter_commands,
    get_command_signature,
    get_help_text,
    plugins,
)
from lightbulb.utils import EmbedNavigator, EmbedPaginator

from Yami.subclasses.plugin import Plugin
from Yami.utils.text import ctx_name


class MyHelpCommand(HelpCommand):
    async def send_help_overview(self, context: Context) -> None:

        plugin_commands = [
            [plugin.name, await filter_commands(context, plugin.commands.values()),]
            for plugin in self.bot.plugins.values()
        ]
        all_plugin_commands = []
        for _, cmds in plugin_commands:
            all_plugin_commands.extend(cmds)
        uncategorized_commands = await filter_commands(
            context, self.bot.commands.difference(set(all_plugin_commands))
        )
        plugin_commands.insert(0, ["Uncategorized", uncategorized_commands])
        help_text = []
        for plugin, commands in plugin_commands:
            if not commands:
                continue
            text = f"{plugin}: "
            text += ", ".join(
                map(
                    lambda command: f"`{command.name}`",
                    sorted(commands, key=lambda c: c.name),
                )
            )
            help_text.append(f"{text}.")
        await self.send_paginated_help(help_text, context)

    @staticmethod
    async def send_paginated_help(text: typing.Sequence[str], context: Context) -> None:

        paginator = EmbedPaginator(max_chars=1028, max_lines=27)

        @paginator.embed_factory()
        def make_embed(index, page):
            return (
                hikari.Embed(
                    title="Help",
                    description=f"Use `{context.prefix}help [command/cog]` for more detailed info.",
                    colour=random.randint(0, 0xFFFFFF),
                    timestamp=datetime.now(tz=timezone.utc),
                )
                .set_footer(
                    text=f"#{index}/{len(paginator)}, Requested by {ctx_name(context)}",
                    icon=context.author.avatar_url,
                )
                .add_field(name="**Available Commands**", value=page)
            )

        for line in text:
            paginator.add_line(line)

        navigator = EmbedNavigator(timeout=30.0, pages=paginator.build_pages())

        await navigator.run(context)

    async def send_command_help(self, context: Context, command: Command) -> None:
        embed = (
            hikari.Embed(
                description=f"**Help for `{command.name}`**",
                colour=random.randint(0, 0xFFFFFF),
                timestamp=datetime.now(tz=timezone.utc),
            )
            .set_footer(
                text=f"Requested by {ctx_name(context)}", icon=context.author.avatar_url
            )
            .add_field(
                name="**Usage**",
                value="```md\n" f"{get_command_signature(command)}" "\n```",
                inline=False,
            )
        )
        if aliases := ", ".join(command.aliases):
            embed.add_field(
                name="**Aliases**", value=f"```md\n{aliases}```", inline=False
            )
        embed.add_field(
            name="Category",
            value=f"```md\n{command.plugin.name if command.plugin else 'Uncategorized'}```",
            inline=False,
        )
        if command_help := get_help_text(command):
            embed.add_field(
                name="**Description**", value=f"```md\n{command_help}```", inline=False,
            )
        await context.reply(embed=embed)

    async def send_group_help(self, context: Context, group: Group) -> None:
        embed = (
            hikari.Embed(
                description=f"**Help for `{group.name}`**",
                colour=random.randint(0, 0xFFFFFF),
                timestamp=datetime.now(tz=timezone.utc),
            )
            .set_footer(
                text=f"Requested by {ctx_name(context)}", icon=context.author.avatar_url
            )
            .add_field(
                name="**Usage**",
                value="```md\n" f"{get_command_signature(group)}" "\n```",
                inline=False,
            )
        )
        if aliases := ", ".join(group.aliases):
            embed.add_field(
                name="**Aliases**", value=f"```md\n{aliases}```", inline=False
            )
        if subcommands := group.subcommands:
            embed.add_field(
                name="**Subcommands**",
                value=f"```md\n{', '.join(map(lambda c: c.name, sorted(subcommands, key=lambda c: c.name)))}\n```",
            )
        embed.add_field(
            name="Category",
            value=f"```md\n{group.plugin.name if group.plugin else 'Uncategorized'}```",
            inline=False,
        )
        if command_help := get_help_text(group):
            embed.add_field(
                name="**Description**", value=f"```md\n{command_help}```", inline=False,
            )
        await context.reply(embed=embed)

    async def send_plugin_help(self, context: Context, plugin: plugins.Plugin) -> None:
        embed = hikari.Embed(
            description=f"**Help for `{plugin.name}`**",
            colour=random.randint(0, 0xFFFFFF),
            timestamp=datetime.now(tz=timezone.utc),
        ).set_footer(
            text=f"Requested by {ctx_name(context)}", icon=context.author.avatar_url
        )
        if help_text := get_help_text(plugin):
            embed.add_field(
                name="**Description**", value=f"```md\n{help_text}\n```", inline=False,
            )
        if commands := plugin.commands:
            embed.add_field(
                name="**Commands**",
                value=f"```md\n{', '.join(map(lambda c: c, sorted(commands.keys(), key=lambda c: c)))}\n```",
            )
        if not embed.fields:
            embed.description += "\n\n No help available."
        await context.reply(embed=embed)


# noinspection PyProtectedMember
class Help(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self._original_help_command = bot._help_impl
        bot._help_impl = MyHelpCommand(bot)
        self.bot.get_command("help").plugin = self.bot.get_plugin("info")

    def plugin_remove(self):
        self.bot._help_impl = self._original_help_command


def load(bot):
    bot.add_plugin(Help(bot))
