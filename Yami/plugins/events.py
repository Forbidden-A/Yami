from datetime import datetime, timezone

import hikari
import typing
from hikari import StartingEvent, GuildCreateEvent, MessageReactionAddEvent, Reaction, ReadyEvent, \
    MessageReactionRemoveEvent
from lightbulb import plugins

from Yami import models
from Yami.subclasses.bot import Bot


class Events(plugins.Plugin):
    def __init__(self, bot: Bot):
        super(Events, self).__init__()
        self.bot: Bot = bot

    @plugins.listener(event_type=StartingEvent)
    async def on_starting(self, event: StartingEvent):
        await self.bot.initialize_database()

    @plugins.listener(event_type=ReadyEvent)
    async def on_ready(self, event: ReadyEvent):
        self.bot.user = event.my_user

    @plugins.listener(event_type=GuildCreateEvent)
    async def on_guild_join(self, event: GuildCreateEvent):
        await models.Guild.get_or_create(id=event.guild.id)

    @staticmethod
    async def get_starboard_embed(message: hikari.Message, created_at: datetime, stars: int) -> typing.Tuple[hikari.Embed, str]:
        channel = await message.fetch_channel()
        embed = hikari.Embed(
            description=f"**[Jump to message!]({message.link})**\n\n{message.content}",
            colour="#F1C40F",
            timestamp=created_at
        ).set_author(
            name=message.author.username,
            icon=message.author.avatar
        ).set_footer(
            text=f"#{channel.name}",
        )
        if message.attachments:
            attachment = message.attachments[0]
            embed.set_image(attachment)

        return embed, f'⭐ {stars} <#{channel.id}>'

    @plugins.listener(event_type=MessageReactionAddEvent)
    async def on_reaction_add(self, event: MessageReactionAddEvent):
        guild, _ = await models.Guild.get_or_create(id=event.guild_id)
        if not guild.starboard:
            return
        if not event.emoji == '⭐':
            return
        # noinspection PyTypeChecker
        starboard: hikari.GuildTextChannel = await self.bot.rest.fetch_channel(guild.starboard)
        message = await self.bot.rest.fetch_message(event.channel_id, event.message_id)
        if message.author.id == event.member.id:
            return await message.remove_reaction(emoji='⭐', user=message.author)
        if message.author.id == self.bot.user.id or event.member.is_bot:
            return
        starred_message_model = await models.StarredMessage.get_or_none(id=event.message_id)
        stars = await self.bot.rest.fetch_reactions_for_emoji(event.channel_id, event.message_id, '⭐').count()
        if starred_message_model:
            starred_message = await self.bot.rest.fetch_message(starboard, starred_message_model.star_id)
            embed, content = await self.get_starboard_embed(message, starred_message.created_at, stars)
            await starred_message.edit(embed=embed, content=content)
        else:
            if stars > 2:
                embed, content = await self.get_starboard_embed(message, datetime.now(timezone.utc), stars)
                starred_message = await starboard.send(embed=embed, content=content)
                await models.StarredMessage.create(id=message.id, star_id=starred_message.id, stars=stars)

    @plugins.listener(event_type=MessageReactionRemoveEvent)
    async def on_reaction_remove(self, event: MessageReactionRemoveEvent):
        guild, _ = await models.Guild.get_or_create(id=event.guild_id)
        if not guild.starboard:
            return
        if not event.emoji == '⭐':
            return
        # noinspection PyTypeChecker
        starboard: hikari.GuildTextChannel = await self.bot.rest.fetch_channel(guild.starboard)
        message = await self.bot.rest.fetch_message(event.channel_id, event.message_id)
        starred_message_model = await models.StarredMessage.get_or_none(id=event.message_id)
        stars = await self.bot.rest.fetch_reactions_for_emoji(event.channel_id, event.message_id, '⭐').count()
        print(stars)
        if starred_message_model:
            starred_message = await self.bot.rest.fetch_message(starboard, starred_message_model.star_id)
            embed, content = await self.get_starboard_embed(message, starred_message.created_at, stars)
            await starred_message.edit(embed=embed, content=content)


def load(bot):
    bot.add_plugin(Events(bot))