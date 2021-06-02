import discord
import asyncio

from os import path
from discord.ext import commands
from urllib.parse import quote_plus

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from model import Image
from config import DB_CONF, BOT_CONF, UPLOAD_DIRECTORY


class Discord2VRCBot(commands.Bot):

    def __init__(self, command_prefix: str, db_conf: dict, bot_conf: dict):
        commands.Bot.__init__(self, command_prefix=command_prefix,
                              owner_ids=set(bot_conf["authorized"]))
        self.valid_channels = set(bot_conf["channel_ids"])
        self._setup_db(db_conf)

    def _setup_db(self, db_conf: dict):
        db_conf["password"] = quote_plus(db_conf["password"])
        client = AsyncIOMotorClient(
            "mongodb://{username}:{password}@{host}:{port}/{database_name}".format(**db_conf))
        self.db = AIOEngine(motor_client=client, database=db_conf["database_name"])

    async def on_command_error(self, ctx, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            await ctx.message.delete()
            await ctx.send("Unknown command", delete_after=3)
        elif isinstance(error, commands.CommandInvokeError):
            if ctx.message:
                try:
                    await ctx.message.delete()
                except:
                    pass
            await ctx.send("Unexpected error, see console log for details", delete_after=3)
            raise error

    async def on_ready(self):
        print('Logged on as', self.user)


if __name__ == "__main__":

    extensions = ["cogs.admin", "cogs.image"]
    bot = Discord2VRCBot(command_prefix="!", db_conf=DB_CONF, bot_conf=BOT_CONF)
    for extension in extensions:
        bot.load_extension(extension)
    bot.run(BOT_CONF["token"])
