import platform
from datetime import datetime, timezone
from random import randint

import aiohttp
import hikari
import lightbulb
import multidict
import typing
from lightbulb import commands, checks, cooldowns
from lightbulb.context import Context

from Yami.converters.guild import guild_converter
from Yami.converters.member import member_converter
from Yami.converters.user import user_converter
from Yami.subclasses.bot import Bot
from Yami.subclasses.plugin import Plugin
from Yami.utils.text import ctx_name, m_name
from Yami.utils.time import display_time_from_delta


class Info(Plugin):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.date_format = "%a, %d, %b %Y"

    @commands.group()
    async def info(self, context: Context):
        return

    @info.command(name="bot")
    async def bot_(self, context: Context):
        """Credits to Yoda#9999"""
        uptime = display_time_from_delta(
            datetime.now(tz=timezone.utc) - self.bot.start_time
        )

        embed = hikari.Embed(
            colour=0x3498DB,
            description=(
                "Yami is a discord bot made using [Hikari](https://nekokatt.github.io/hikari/) and [Lightbulb](https://tandemdude.gitlab.io/lightbulb/)\n"
                "[Hikari Discord](https://discord.com/invite/Jx4cNGG)\n"
                "[Hikari Docs](https://nekokatt.github.io/hikari/hikari/index.html)\n"
                "[Hikari Github](https://github.com/nekokatt/hikari)\n"
                "[Hikari PyPi](https://pypi.org/project/hikari/)\n"
                "[Lightbulb Docs](https://tandemdude.gitlab.io/lightbulb/)\n"
                "[Lightbulb Gitlab](https://gitlab.com/tandemdude/lightbulb)\n"
                "[Lightbulb PyPi](https://pypi.org/project/hikari-lightbulb/)\n"
                "[Yami](https://github.com/Forbidden-A/Yami)"
            ),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Hikari Version", value=hikari.__version__, inline=False)
        embed.add_field(name="Aiohttp Version", value=aiohttp.__version__, inline=False)
        # noinspection PyUnresolvedReferences
        embed.add_field(
            name="MultiDict Version", value=multidict.__version__, inline=False
        )
        embed.add_field(
            name="Lightbulb Version", value=lightbulb.__version__, inline=False
        )
        embed.add_field(
            name="Python Version", value=platform.python_version(), inline=False
        )
        embed.add_field(name="Uptime", value=uptime, inline=False)
        await context.reply(embed=embed)

    @commands.group(aliases=["in", "i"])
    async def inspect(self, context: Context):
        return

    @checks.guild_only()
    @cooldowns.cooldown(length=30, usages=3, bucket=cooldowns.UserBucket)
    @inspect.command(aliases=["m", "mem"])
    async def member(self, context: Context, member: member_converter = None):
        now = datetime.now(tz=timezone.utc)
        member: hikari.Member = member or context.member
        roles = self.bot.cache.get_roles_view_for_guild(
            context.guild_id
        ).values() or await self.bot.rest.fetch_roles(context.guild_id)
        roles = sorted(
            [r for r in roles if r.id in member.role_ids],
            key=lambda r: r.position,
            reverse=True,
        )
        coloured_roles = list(filter(lambda r: r.colour.hex_code != "#000000", roles))
        created_at = member.created_at.astimezone(timezone.utc)
        created_at = f"{created_at.strftime(self.date_format)}. {display_time_from_delta((now - created_at), granularity=2)} ago."
        joined_at = member.joined_at.astimezone(timezone.utc)
        joined_at = f"{joined_at.strftime(self.date_format)}. {display_time_from_delta((now - joined_at), granularity=2)} ago."
        embed = (
            hikari.Embed(
                title="Inspect Member",
                description=f"**Name:** `{member.username}`\n"
                f"**Discriminator:** `{member.discriminator}`\n"
                f"**ID:** `{member.id}`\n"
                f"**Account Type:** `{'Bot' if member.is_bot else 'Human'}`\n"
                f"**Joined Discord:** `{created_at}`\n"
                f"**Joined here:** `{joined_at}`\n"
                f"**Display Name:** `{m_name(member)}`\n"
                f"**Nickname:** `{member.nickname}`\n"
                f"**Rank:** {f'<@&{roles[0].id}>' if roles else '@everyone'}\n"
                f"**• Member colour:** `{coloured_roles[0].colour.hex_code.upper() if coloured_roles else '#000000'}`\n",
                timestamp=now,
                colour=coloured_roles[0].colour
                if coloured_roles
                else randint(0, 0xFFF),
            )
            .add_field(
                inline=False,
                name=f"Roles [{len(roles)}]",
                value=", ".join([f"<@&{role.id}>" for role in roles]) or "@everyone",
            )
            .set_thumbnail(member.avatar_url)
            .set_footer(
                text=f"Requested by {ctx_name(context)}",
                icon=context.member.avatar_url,
            )
        )
        await context.reply(embed=embed)

    @cooldowns.cooldown(length=30, usages=3, bucket=cooldowns.UserBucket)
    @inspect.command(aliases=["u"])
    async def user(self, context: Context, user: user_converter = None):
        user: hikari.User = user or context.author
        now = datetime.now(tz=timezone.utc)

        created_at = user.created_at.astimezone(timezone.utc)

        created_at = f"{created_at.strftime(self.date_format)}. {display_time_from_delta((now - created_at), granularity=2)} ago."
        embed = (
            hikari.Embed(
                title="Inspect User",
                colour=randint(0, 0xFFF),
                description=f"**Name:** `{user.username}`\n"
                f"**Discriminator:** `{user.discriminator}`\n"
                f"**ID:** `{user.id}`\n"
                f"**Joined Discord:** `{created_at}`\n"
                f"**Account Type:** `{'Bot' if user.is_bot else 'Human'}`\n",
                timestamp=now,
            )
            .set_thumbnail(user.avatar_url)
            .set_footer(
                text=f"Requested by {ctx_name(context)}", icon=context.author.avatar_url
            )
        )
        await context.reply(embed=embed)

    @cooldowns.cooldown(length=30, usages=3, bucket=cooldowns.UserBucket)
    @inspect.command(aliases=["g", "gld"])
    async def guild(self, context: Context, guild_id: guild_converter = None):
        guild: typing.Union[hikari.GatewayGuild, hikari.RESTGuild] = guild_id or (
            self.bot.cache.get_guild(context.guild_id)
            or await self.bot.rest.fetch_guild(context.guild_id)
        ) if context.guild_id else None

        if guild is None:
            return context.reply("Please provide a guild.")

        now = datetime.now(tz=timezone.utc)

        created_at = guild.created_at.astimezone(timezone.utc)

        created_at = f"{created_at.strftime(self.date_format)}. {display_time_from_delta((now - created_at), granularity=2)} ago."
        roles = self.bot.cache.get_roles_view_for_guild(
            guild.id
        ).values() or await self.bot.rest.fetch_roles(guild.id)
        roles = sorted(
            [r for r in roles if r.position != 0],
            key=lambda r: r.position,
            reverse=True,
        )
        roles_names_or_mentions = (
            [f"<@&{role.id}>" for role in roles]
            if guild.id == context.guild_id
            else [role.name for role in roles]
        )
        await context.reply(
            hikari.Embed(
                title="Inspect Guild",
                colour=randint(0, 0xFFFFFF),
                timestamp=now,
                description=f"**Name:** `{guild.name}`\n"
                f"**ID:** `{guild.id}`\n"
                f"**Owner:** `{self.bot.cache.get_user(guild.owner_id) or await self.bot.rest.fetch_user(guild.owner_id)}`\n"
                f"**Members:** `{len(guild.members)}`\n"
                f"**• Humans:** `{len([member for member in guild.members.values() if not member.is_bot])}`\n"
                f"**• Bots:** `{len([member for member in guild.members.values() if member.is_bot])}`\n"
                f"**Roles:** `{len(guild.roles)}`\n"
                f"**Emojis:** `{len(guild.emojis)}`\n"
                f"**Created at:** `{created_at}`\n"
                f"**Channels:** `{len(guild.channels)}`\n"
                f"**• Categories:** `{len(list(filter(lambda channel: isinstance(channel, hikari.GuildCategory), guild.channels.values())))}`\n"
                f"**• Text:** `{len(list(filter(lambda channel: isinstance(channel, hikari.GuildTextChannel), guild.channels.values())))}`\n"
                f"**• Voice:** `{len(list(filter(lambda channel: isinstance(channel, hikari.GuildVoiceChannel), guild.channels.values())))}`\n"
                f"**Region:** `{guild.region}`\n"
                f"**AFK Channel:** {f'<#{guild.afk_channel_id}>' if guild.afk_channel_id else '`None`'}\n"
                f"**AFK Timeout:** `{guild.afk_timeout}`\n"
                f"**System Channel:** <#{guild.system_channel_id}>\n"
                f"**MFA Enforced:** `{'Yes' if guild.mfa_level else 'No'}`\n"
                f"**Verification Level:** `{guild.verification_level}`",
            )
            .set_footer(
                text=f"Requested by {ctx_name(context)}",
                icon=context.member.avatar_url,
            )
            .set_thumbnail(guild.icon_url)
            .add_field(
                inline=False,
                name=f"Roles [{len(roles)}]",
                value=", ".join(roles_names_or_mentions) or "@everyone",
            )
        )


def load(bot):
    bot.add_plugin(Info(bot))
