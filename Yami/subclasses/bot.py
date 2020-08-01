import os
import traceback

import hikari
import lightbulb
from tortoise import Tortoise


class Bot(lightbulb.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: hikari.User = None

    async def initialize_database(self):
        if db_url := os.getenv("YAMI_DB_URL"):
            await Tortoise.init(db_url=db_url, modules={"models": ["Yami.models"]})
            await Tortoise.generate_schemas()
        else:
            print(
                "Please set an environment variable called `YAMI_DB_URL` and set its value to the DB url.",
                "\n format is as follows `postgres://{username}:{password}@{host}:{port}/{db}`",
            )

    def load_extensions(self):
        for extension in os.listdir("plugins"):
            try:
                if extension.endswith(".py"):
                    self.load_extension(f"Yami.plugins.{extension[:-3]}")
                    print(f"Loaded extension {extension[:-3]}")
                else:
                    print(extension, "is not a python file.")
            except lightbulb.errors.ExtensionMissingLoad:
                print(extension, "is missing load function.")
            except lightbulb.errors.ExtensionAlreadyLoaded:
                pass
            except lightbulb.errors.ExtensionError as e:
                print(extension, "Failed to load.")
                print(
                    "".join(
                        traceback.format_exception(
                            type(e or e.__cause__), e or e.__cause__, e.__traceback__
                        )
                    )
                )

    async def close(self) -> None:
        await Tortoise.close_connections()
        await super(Bot, self).close()
