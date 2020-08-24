import asyncio
import collections
import contextlib
import importlib
import inspect
import io
import logging
import platform
import re
import textwrap
import traceback
import typing
from datetime import datetime, timezone
from random import randint

import hikari
import lightbulb
from lightbulb import Context, checks, commands, plugins
from lightbulb.utils import EmbedNavigator, EmbedPaginator

from Yami.converters.command import command_or_plugin_converter
from Yami.subclasses.plugin import Plugin
from Yami.utils.text import ctx_name


def maybe_import(lib):
    # noinspection PyBroadException
    try:
        module = importlib.import_module(lib)
        return module
    except Exception:
        return None


class _ModuleDict(collections.OrderedDict):
    """Used internally to make """

    def __str__(self):
        k: str
        return f"ModuleDict({{{','.join(str(k) for k in self.keys())}}})"

    __repr__ = __str__


modules = _ModuleDict(
    {
        "aiohttp": maybe_import("aiohttp"),
        "async_timeout": maybe_import("async_timeout"),
        "asyncio": maybe_import("asyncio"),
        "collections": maybe_import("collections"),
        "dataclasses": maybe_import("dataclasses"),
        "decimal": maybe_import("decimal"),
        "functools": maybe_import("functools"),
        "hashlib": maybe_import("hashlib"),
        "inspect": maybe_import("inspect"),
        "io": maybe_import("io"),
        "json": maybe_import("json"),
        "math": maybe_import("math"),
        "os": maybe_import("os"),
        "random": maybe_import("random"),
        "re": maybe_import("re"),
        "requests": maybe_import("requests"),
        "statistics": maybe_import("statistics"),
        "sys": maybe_import("sys"),
        "textwrap": maybe_import("textwrap"),
        "urllib": maybe_import("urllib"),
        "urlparse": maybe_import("urllib.parse"),
        "weakref": maybe_import("weakref"),
        "bs4": maybe_import("bs4"),
        "subprocess": maybe_import("subprocess"),
        "time": maybe_import("time"),
        "datetime": maybe_import("datetime"),
        "hikari": maybe_import("hikari"),
        "lightbulb": maybe_import("lightbulb"),
        "PIL": maybe_import("PIL"),
    }
)


# noinspection PyProtectedMember
class SuperUser(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.pattern = re.compile(r"```(?P<syntax>.*)\n(?P<body>[^`]+?)```")
        self.last_result = None

    @staticmethod
    def get_syntax_error(error: SyntaxError) -> str:
        """return syntax error string from error"""
        if error.text is None:
            return f"{error.__class__.__name__}: {error}\n"
        return f'{error.text}{"^":>{error.offset}}\n{type(error).__name__}: {error}'

    def clean(self, body):
        if match := self.pattern.search(body):
            items = match.groupdict()
            return items["body"]
        return body

    @staticmethod
    def wrap(body):
        return "async def __invoke__(bot, context):\n" + textwrap.indent(body, " " * 4)

    async def evaluate(self, context: Context, body):
        success = False
        start = datetime.now(tz=timezone.utc)
        body = self.wrap(self.clean(body))
        stack = contextlib.ExitStack()
        stream = io.StringIO()
        stack.enter_context(contextlib.redirect_stdout(stream))
        stack.enter_context(contextlib.redirect_stderr(stream))
        stream_handler = logging.StreamHandler(stream)
        self.logger.addHandler(stream_handler)
        with stack:
            try:
                env: typing.Dict[str, typing.Optional[typing.Any]] = {
                    "self": self,
                    "ctx": context,
                    "channel_id": context.channel_id,
                    "channel": context.bot.cache.get_guild_channel(context.channel_id),
                    "author": context.author,
                    "member": context.member,
                    "guild": context.bot.cache.get_guild(context.guild_id),
                    "guild_id": context.guild_id,
                    "message": context.message,
                    "_": self.last_result,
                }

                env.update(globals())
                env.update(locals())
                env.update(modules)
                exec(body, env)
                self.last_result = await env["__invoke__"](context.bot, context)
                stream.write(f"- Returned: {self.last_result!r}")
            except SyntaxError as e:
                stream.write(self.get_syntax_error(e))
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
            else:
                success = True
                self.logger.removeHandler(stream_handler)

        stream.seek(0)
        lines = (
            "\n".join(stream.readlines())
            .replace(context.bot._token, "~TOKEN~")
            .replace("`", "´")
        )
        paginator = EmbedPaginator(
            max_lines=27, prefix="```diff\n", suffix="```", max_chars=1048
        )

        @paginator.embed_factory()
        def make_page(index, page):
            return hikari.Embed(
                title=f"Executed in {(datetime.now(tz=timezone.utc) - start).total_seconds() * 1000:.2f}ms",
                colour=0x58EF92 if success else 0xE74C3C,
                description=f"Result: {page}",
                timestamp=datetime.now(tz=timezone.utc),
            ).set_footer(
                text=f"#{index}/{len(paginator)}, Requested by {ctx_name(context)}",
                icon=context.author.avatar_url,
            )

        paginator.add_line(
            f"*** Python {platform.python_version()} - Hikari {hikari.__version__} - lightbulb {lightbulb.__version__}\n"
            + lines
        )

        navigator = EmbedNavigator(pages=paginator.build_pages())
        await navigator.run(context)

    async def execute_in_shell(self, context: Context, body):
        start = datetime.now(tz=timezone.utc)
        body = self.clean(body)
        stack = contextlib.ExitStack()
        stream = io.StringIO()
        stack.enter_context(contextlib.redirect_stdout(stream))
        stack.enter_context(contextlib.redirect_stderr(stream))

        with stack:
            process = await asyncio.create_subprocess_shell(
                body, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            stream.write(stdout.decode())
            stream.write(stderr.decode())

        stream.write(f"\n- Return code {process.returncode}")
        stream.seek(0)
        lines = (
            "\n".join(stream.readlines())
            .replace(context.bot._token, "~TOKEN~")
            .replace("`", "´")
        )

        paginator = EmbedPaginator(
            max_lines=27, prefix="```diff\n", suffix="```", max_chars=1048
        )

        @paginator.embed_factory()
        def make_page(index, page):
            return hikari.Embed(
                title=f"Executed in {(datetime.now(tz=timezone.utc) - start).total_seconds() * 1000:.2f}ms",
                colour=0x58EF92 if process.returncode == 0 else 0xE74C3C,
                description=f"Result: {page}",
                timestamp=datetime.now(tz=timezone.utc),
            ).set_footer(
                text=f"#{index}/{len(paginator)}, Requested by {ctx_name(context)}",
                icon=context.author.avatar_url,
            )

        paginator.add_line(
            f"*** Python {platform.python_version()} - Hikari {hikari.__version__} - lightbulb {lightbulb.__version__}\n"
            + lines
        )

        navigator = EmbedNavigator(pages=paginator.build_pages())
        await navigator.run(context)

    # noinspection PyUnusedLocal
    @checks.owner_only()
    @commands.command(aliases=["sh", "shell", "exec", "eval", "evaluate"])
    async def execute(self, context: Context, *, content):
        def check(event):
            return event.message.id == context.message.id

        await self.execute_in_shell(
            context=context,
            body=context.message.content.lstrip(
                f"{context.prefix}{context.invoked_with}"
            ),
        ) if context.invoked_with in ("sh", "shell") else await self.evaluate(
            context=context,
            body=context.message.content.lstrip(
                f"{context.prefix}{context.invoked_with}"
            ),
        )
        try:
            message_event = await context.bot.wait_for(
                hikari.events.MessageUpdateEvent, timeout=60.0, predicate=check
            )
            if message_event.message.content != context.message.content:
                new_message = await context.bot.rest.fetch_message(
                    message_event.message.channel_id, message_event.message.id,
                )
                new_message.guild_id = context.guild_id
                command_context = Context(
                    context.bot,
                    new_message,
                    context.prefix,
                    context.invoked_with,
                    context.command,
                )
                # noinspection PyTypeChecker
                command_args = context.bot.resolve_arguments(
                    message_event.message, context.prefix
                )[1:]
                channel = context.bot.cache.get_guild_channel(
                    context.channel_id
                ) or await context.bot.rest.fetch_channel(context.channel_id)
                # noinspection PyProtectedMember
                await context.bot._invoke_command(
                    context.command, command_context, command_args
                )
        except (hikari.ForbiddenError, hikari.NotFoundError):
            pass
        except asyncio.TimeoutError:
            pass

    @checks.owner_only()
    @commands.command(aliases=["p"])
    async def panic(self, context: Context):
        m = await context.reply("Panicking..")
        context.bot.remove_plugin(self.name)
        await m.edit("Panicked")

    @checks.owner_only()
    @commands.command(aliases=["rst"])
    async def restart(self, context: Context):
        await context.reply("Ja, matane")
        asyncio.create_task(context.bot.close())

    @checks.owner_only()
    @commands.command(aliases=["showcode", "codefor", "code", "source"])
    async def getcode(
        self, context: Context, child: command_or_plugin_converter = None
    ):
        child: typing.Union[plugins.Plugin, commands.Command] = child or context.command
        if isinstance(child, plugins.Plugin):
            code = inspect.getsource(child.__class__)
        else:
            code = inspect.getsource(child._callback)
        lines = "\n".join([line for line in code.splitlines()]).replace("`", "ˋ")
        paginator = EmbedPaginator(prefix="```py\n", suffix="```", max_lines=20)

        @paginator.embed_factory()
        def make_embed(index, page):
            return hikari.Embed(
                title=f"Code for {child.name}",
                description=page,
                colour=randint(0, 0xFFF),
                timestamp=datetime.now(tz=timezone.utc),
            ).set_footer(
                text=f"#{index}/{len(paginator)}, Requested by {ctx_name(context)}",
                icon=context.author.avatar_url,
            )

        paginator.add_line(lines)
        navigator = EmbedNavigator(paginator.build_pages())
        await navigator.run(context)


def load(bot):
    bot.add_plugin(SuperUser(bot))
