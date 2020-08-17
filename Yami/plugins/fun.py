import io

import aiohttp
from lightbulb import commands, Context

from Yami.subclasses.bot import Bot
from Yami.subclasses.plugin import Plugin


class Fun(Plugin):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    @commands.command()
    async def thumbnail(self, context: Context, query):

        if "v=" in query:
            video_id: str = query.split('v=')[1]

            if "&" in video_id:
                ampersand_position = video_id.index('&')

                if ampersand_position != -1:
                    video_id = video_id[:ampersand_position]
        else:
            video_id = query
        async with aiohttp.request("get", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg") as resp:
            if resp.status == 404:
                async with aiohttp.request("get", f"https://img.youtube.com/vi/{video_id}/default.jpg") as resp_:
                    if resp_.status == 404:
                        return await context.reply("Invalid Youtube video.")
                    elif resp_.status == 200:
                        bio = io.BytesIO()
                        bio.write(await resp_.read())
                        bio.seek(0)
                        return await context.reply(bio.read())
                    else:
                        await context.reply("Unknown error occurred.")
            elif resp.status == 200:
                bio = io.BytesIO()
                bio.write(await resp.read())
                bio.seek(0)
                return await context.reply(bio.read())
            else:
                await context.reply("Unknown error occurred.")


def load(bot):
    bot.add_plugin(Fun(bot))
