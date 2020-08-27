import logging
import logging.config
import os
import typing

import hikari

from Yami import models
from Yami.subclasses.bot import Bot


async def get_prefix(bot, message: hikari.Message) -> typing.List[str]:
    if not message.guild_id:
        return [f"{bot.user.mention} ", "y."]
    else:
        guild = await models.Guild.get(id=message.guild_id)
        return [f"{bot.user.mention} ", guild.prefix]


def main():
    # Set path to bot directory
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)
    logger = logging.getLogger("Yami")
    if token := os.getenv("YAMI_TOKEN"):
        bot = Bot(
            prefix=get_prefix,
            token=token,
            insensitive_commands=True,
            logger=logger,
            stateless=False,
            logging_level=logging.WARNING,
            intents=hikari.Intents.ALL,
        )
        logger.setLevel(logging.INFO)
        bot.load_extensions()
        bot.run()
    else:
        logger.error(
            "Please set an environment variable called `YAMI_TOKEN` and set its value to the bot's token."
        )


if __name__ == "__main__":
    main()
