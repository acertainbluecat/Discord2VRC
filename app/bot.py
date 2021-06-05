import json
import uvloop
import discord
import traceback

from typing import List

from discord.ext import commands

from common.config import config
from common.database import Mongo


class Discord2VRCBot(commands.Bot):
    def __init__(self, command_prefix: str, owner_ids: List[int]):
        commands.Bot.__init__(
            self, command_prefix=command_prefix, owner_ids=set(owner_ids)
        )
        Mongo.connect()
        self._setup_cogs()

    def _setup_cogs(self):
        with open("cogs/cogs.json") as json_file:
            cogs = json.load(json_file)
            for cog in cogs["loaded"]:
                try:
                    self.load_extension(cog)
                except (discord.ClientException, ModuleNotFoundError):
                    print(f"Failed to load cog {cog}.")
                    traceback.print_exc()

    async def on_command_error(self, ctx, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            await ctx.message.delete()
            await ctx.send("Unknown command", delete_after=3)
        elif isinstance(error, commands.CommandInvokeError):
            if ctx.message:
                try:
                    await ctx.message.delete()
                except discord.NotFound:
                    pass
            await ctx.send(
                f"Error: {type(error).__name__} - {error}", delete_after=5
            )
            raise error

    async def on_ready(self):
        print("Logged on as", self.user)


if __name__ == "__main__":

    uvloop.install()
    bot = Discord2VRCBot(
        command_prefix="!", owner_ids=config["discord"]["owners"]
    )
    bot.run(config["discord"]["token"])
