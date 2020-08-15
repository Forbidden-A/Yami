import asyncio
import collections
import contextlib
import importlib
import io
import logging
import platform
import re
import textwrap
import traceback
from datetime import timezone, datetime
import hikari
import lightbulb
import typing
from lightbulb import Context, commands, checks
from lightbulb.utils import EmbedPaginator, EmbedNavigator
from tortoise import Tortoise

from Yami.subclasses.plugin import Plugin


def maybe_import(lib):
    # noinspection PyBroadException
    try:
        module = importlib.import_module(lib)
        return module
    except Exception as ex:
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
        "PIL": maybe_import("PIL")
    }
)


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
        stream_handler.setFormatter(self.bot.logger.handlers[0].formatter)
        self.logger.addHandler(stream_handler)
        with stack:
            try:
                env: typing.Dict[str, typing.Optional[typing.Any]] = {
                    "self": self,
                    "ctx": context,
                    "channel_id": context.channel_id,
                    "channel": self.bot.cache.get_guild_channel(context.channel_id),
                    "author": context.author,
                    "member": context.member,
                    "guild": self.bot.cache.get_guild(context.guild_id),
                    "guild_id": context.guild_id,
                    "message": context.message,
                    "_": self.last_result
                }

                env.update(globals())
                env.update(locals())
                env.update(modules)
                exec(body, env)
                self.last_result = await env["__invoke__"](self.bot, context)
                stream.write(f"- Returned: {self.last_result!r}")
            except SyntaxError as e:
                stream.write(self.get_syntax_error(e))
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
            else:
                success = True
                self.logger.removeHandler(stream_handler)

        stream.seek(0)
        lines = "\n".join(stream.readlines()).replace(self.bot._token, "~TOKEN~").replace("`", "´")
        paginator = EmbedPaginator(max_lines=27, prefix="```diff\n", suffix="```", max_chars=1048)

        @paginator.embed_factory()
        def make_page(index, page):
            return hikari.Embed(
                title=f"Executed in {(datetime.now(tz=timezone.utc) - start).total_seconds() * 1000:.2f}ms",
                colour=0x58EF92 if success else 0xE74C3C,
                description=f"Result: {page}",
                timestamp=datetime.now(tz=timezone.utc)
            ).set_footer(
                text=f"#{index}/{len(paginator)}, Requested by {context.message.member.nickname or context.author.username if context.member else context.author.username}",
                icon=context.author.avatar
            )

        paginator.add_line(
            f"*** Python {platform.version()} - Hikari {hikari.__version__} - lightbulb {lightbulb.__version__}\n" + lines)

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
                body, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            stream.write(stdout.decode())
            stream.write(stderr.decode())

        stream.write(f"\n- Return code {process.returncode}")
        stream.seek(0)
        lines = "\n".join(stream.readlines()).replace(self.bot._token, "~TOKEN~").replace("`", "´")

        paginator = EmbedPaginator(max_lines=27, prefix='```diff\n', suffix='```', max_chars=1048)

        @paginator.embed_factory()
        def make_page(index, page):
            return hikari.Embed(
                title=f"Executed in {(datetime.now(tz=timezone.utc) - start).total_seconds() * 1000:.2f}ms",
                colour=0x58EF92 if process.returncode == 0 else 0xE74C3C,
                description=f"Result: {page}",
                timestamp=datetime.now(tz=timezone.utc)
            ).set_footer(
                text=f"#{index}/{len(paginator)}, Requested by {context.message.member.nickname or context.author.username if context.member else context.author.username}",
                icon=context.author.avatar
            )

        paginator.add_line(
            f"*** Python {platform.version()} - Hikari {hikari.__version__} - lightbulb {lightbulb.__version__}\n" + lines)

        navigator = EmbedNavigator(pages=paginator.build_pages())
        await navigator.run(context)

    @checks.owner_only()
    @commands.command(aliases=["sh", "shell", "exec", "eval", "evaluate"])
    async def execute(self, context: Context, *, content):
        sent = []

        async def new_send(*args, **kwargs):
            result = await self.bot.send(*args, **kwargs)
            sent.append(result) if result.channel_id == context.channel_id else ...
            return result

        self.bot.rest.create_message = new_send

        async def check(event):
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
                new_message = await self.bot.rest.fetch_message(
                    message_event.message.channel_id, message_event.message.id,
                )
                new_message.guild_id = context.guild_id
                command_context = Context(
                    self.bot,
                    new_message,
                    context.prefix,
                    context.invoked_with,
                    context.command,
                )
                command_args = self.bot.resolve_arguments(
                    message_event.message, context.prefix
                )[1:]
                for message in sent:
                    await message.delete()
                # noinspection PyProtectedMember
                await self.bot._invoke_command(
                    context.command, command_context, command_args
                )
        except (hikari.ForbiddenError, hikari.NotFoundError):
            pass
        except asyncio.TimeoutError:
            pass
        self.bot.rest.create_message = self.bot.send

    @checks.owner_only()
    @commands.command(aliases=['p'])
    async def panic(self, context: Context, arg=""):
        if "-h" in arg:
            await context.reply("Panicking hard!")
            await Tortoise.close_connections()
            exit(0)

        await context.reply("Panicking..")
        self.bot.remove_plugin(self.name)

    @checks.owner_only()
    @commands.command(aliases=["restart"])
    async def shutdown(self, context: Context):
        await Tortoise.close_connections()
        exit(0)


def load(bot):
    bot.add_plugin(SuperUser(bot))
