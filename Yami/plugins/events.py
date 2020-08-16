import typing
from datetime import datetime, timezone

import hikari
from hikari import (
    StartingEvent,
    ShardReadyEvent,
    GuildAvailableEvent,
    ReactionDeleteEvent,
    ReactionAddEvent,
    NotFoundError,
)
from lightbulb import plugins

from Yami import models
from Yami.subclasses.bot import Bot
from Yami.subclasses.plugin import Plugin


class Events(Plugin):
    def __init__(self, bot: Bot):
        super(Events, self).__init__(bot)

    @plugins.listener(event_type=StartingEvent)
    async def on_starting(self, event: StartingEvent):
        await self.bot.initialize_database()

    @plugins.listener(event_type=ShardReadyEvent)
    async def on_ready(self, event: ShardReadyEvent):
        self.bot.user = event.my_user

    @plugins.listener(event_type=GuildAvailableEvent)
    async def on_guild_join(self, event: GuildAvailableEvent):
        await models.Guild.get_or_create(id=event.guild.id)

    @staticmethod
    async def get_starboard_embed(
        message: hikari.Message, guild_id, created_at: datetime, stars: int
    ) -> typing.Tuple[hikari.Embed, str]:
        channel = await message.fetch_channel()
        embed = (
            hikari.Embed(
                description=f"**[Jump to message!]({message.link.replace('@me', str(guild_id))})**\n\n{message.content}",
                colour="#F1C40F",
                timestamp=created_at,
            )
            .set_author(name=message.author.username, icon=message.author.avatar)
            .set_footer(text=f"#{channel.name}",)
        )
        if message.attachments:
            attachment = message.attachments[0]
            embed.set_image(attachment)

        return embed, f"⭐ {stars} <#{channel.id}>"

    @plugins.listener(event_type=ReactionAddEvent)
    async def on_reaction_add(self, event: ReactionAddEvent):
        guild, _ = await models.Guild.get_or_create(id=event.guild_id)
        if not guild.starboard or not event.emoji == "⭐":
            return

        # noinspection PyTypeChecker
        starboard: hikari.GuildTextChannel = await self.bot.rest.fetch_channel(
            guild.starboard
        )

        message = await self.bot.rest.fetch_message(event.channel_id, event.message_id)

        if (
            message.author.id == event.user_id
            or message.author.id == self.bot.user.id
            or event.member.is_bot
        ):
            return await message.remove_reaction(emoji="⭐", user=message.author)

        starred_message_model = await models.StarredMessage.get_or_none(
            id=event.message_id
        )

        stars = await self.bot.rest.fetch_reactions_for_emoji(
            event.channel_id, event.message_id, "⭐"
        ).count()

        if starred_message_model:
            try:
                starred_message = await self.bot.rest.fetch_message(
                    starboard, starred_message_model.star_id
                )
            except NotFoundError:
                await starred_message_model.delete()
                return

            embed, content = await self.get_starboard_embed(
                message, guild.id, starred_message.created_at, stars
            )

            starred_message_model.stars = stars
            await starred_message_model.save()

            await starred_message.edit(embed=embed, content=content)

        else:

            if stars >= 2:

                embed, content = await self.get_starboard_embed(
                    message, guild.id, datetime.now(timezone.utc), stars
                )

                starred_message = await starboard.send(embed=embed, content=content)

                await models.StarredMessage.create(
                    id=message.id, star_id=starred_message.id, stars=stars
                )

    @plugins.listener(event_type=ReactionDeleteEvent)
    async def on_reaction_remove(self, event: ReactionDeleteEvent):
        guild, _ = await models.Guild.get_or_create(id=event.guild_id)

        if not guild.starboard or not event.emoji == "⭐":
            return

        # noinspection PyTypeChecker
        starboard: hikari.GuildTextChannel = await self.bot.rest.fetch_channel(
            guild.starboard
        )

        message = await self.bot.rest.fetch_message(event.channel_id, event.message_id)

        if event.user_id == message.author.id:
            return

        starred_message_model = await models.StarredMessage.get_or_none(
            id=event.message_id
        )

        stars = await self.bot.rest.fetch_reactions_for_emoji(
            event.channel_id, event.message_id, "⭐"
        ).count()

        if starred_message_model and stars > starred_message_model.stars:

            try:
                starred_message = await self.bot.rest.fetch_message(
                    starboard, starred_message_model.star_id
                )
            except NotFoundError:
                await starred_message_model.delete()
                return
            embed, content = await self.get_starboard_embed(
                message, guild.id, starred_message.created_at, stars
            )
            starred_message_model.stars = stars
            await starred_message_model.save()
            await starred_message.edit(embed=embed, content=content)


def load(bot):
    bot.add_plugin(Events(bot))
