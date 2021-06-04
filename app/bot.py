import json
import uvloop
import discord
import traceback

from os import path
from discord.ext import commands
from urllib.parse import quote_plus

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from common.config import BOT_CONF
from common.database import Mongo

class Discord2VRCBot(commands.Bot):

    def __init__(self, command_prefix: str):
        commands.Bot.__init__(self, command_prefix=command_prefix,
                              owner_ids=set(BOT_CONF["authorized"]))
        Mongo.connect()
        self._setup_cogs()

    def _setup_cogs(self):
        with open("cogs/cogs.json") as json_file:
            cogs = json.load(json_file)
            for cog in cogs["loaded"]:
                try:
                    self.load_extension(cog)
                except (discord.ClientException, ModuleNotFoundError):
                    print(f'Failed to load cog {cog}.')
                    traceback.print_exc()

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
            await ctx.send(f'Error: {type(error).__name__} - {error}', delete_after=5)
            raise error

    async def on_ready(self):
        print('Logged on as', self.user)


if __name__ == "__main__":

    uvloop.install()
    bot = Discord2VRCBot(command_prefix="!")
    bot.run(BOT_CONF["token"])
