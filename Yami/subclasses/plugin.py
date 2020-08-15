import logging

from lightbulb import plugins

from Yami.subclasses.bot import Bot


class Plugin(plugins.Plugin):
    def __init__(self, bot: Bot, *, logger: logging.Logger = None, name: str = None):
        super().__init__(name=name)
        self.bot = bot
        self.logger = logger or logging.getLogger(f"Yami.plugins.{self.name}")
