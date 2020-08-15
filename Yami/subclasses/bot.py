import logging
import os
import traceback

import hikari
import lightbulb
import typing
from tortoise import Tortoise


class Bot(lightbulb.Bot):
    def __init__(self, *args, logger=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: typing.Optional[hikari.User] = None
        self.logger = logger or logging.getLogger(__name__)
        self.send = self.rest.create_message

    async def initialize_database(self):
        if db_url := os.getenv("YAMI_DB_URL"):
            await Tortoise.init(db_url=db_url, modules={"models": ["Yami.models"]})
            await Tortoise.generate_schemas()
        else:
            self.logger.error(
                "Please set an environment variable called `YAMI_DB_URL` and set its value to the DB url.",
                "\n format is as follows `postgres://{username}:{password}@{host}:{port}/{db}`",
            )
            exit(-1)

    def load_extensions(self):
        for extension in os.listdir("plugins"):
            try:
                if extension.endswith(".py"):
                    self.load_extension(f"Yami.plugins.{extension[:-3]}")
                    self.logger.info(f"Loaded extension %s", extension[:-3])
                else:
                    self.logger.info("%s is not a python file.", extension)
            except lightbulb.errors.ExtensionMissingLoad:
                self.logger.warning("%s is missing load function.", extension)
            except lightbulb.errors.ExtensionAlreadyLoaded:
                pass
            except lightbulb.errors.ExtensionError as e:
                self.logger.error("%s Failed to load.", extension)
                self.logger.error(
                    "\n"
                    "".join(
                        traceback.format_exception(
                            type(e or e.__cause__), e or e.__cause__, e.__traceback__
                        )
                    )
                )

    async def close(self) -> None:
        await Tortoise.close_connections()
        await super().close()
