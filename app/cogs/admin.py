import json
import discord
import asyncio

from os import listdir
from typing import Optional
from discord.ext import commands


class AdminCog(commands.Cog, name="Admin"):
    """This extension handles some basic administrative commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _prefix_cog(self, name: str) -> str:
        """Prefixes cog names with cog."""
        if name.startswith("cogs."):
            return name.lower()
        return "cogs." + name.lower()

    def _strip_cog(self, name: str) -> str:
        """Strips cog. from cog names"""
        return name.lstrip("cogs.")

    def enumerate_extensions(self) -> set:
        """Enumerate .py files in cogs directory"""
        return {
            f.replace(".py", "") for f in listdir("cogs") if f.endswith(".py")
        }

    def save_loaded_extensions(self) -> None:
        """Saves currently loaded extensions for future runs"""
        with open("cogs/cogs.json", "w") as json_file:
            json.dump({"loaded": list(self.bot.extensions.keys())}, json_file)

    async def cog_check(self, ctx) -> bool:
        """discord cog check function"""
        if ctx.guild is None:
            return False
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def load(self, ctx, cog: str) -> None:
        """Load extension, eg. !load image"""
        await ctx.message.delete()
        try:
            self.bot.load_extension(self._prefix_cog(cog))
        except commands.ExtensionAlreadyLoaded:
            await ctx.send("Extension is already loaded", delete_after=3)
        except commands.ExtensionNotFound:
            await ctx.send("Extension not found", delete_after=3)
        except Exception as e:
            await ctx.send(f"Error: {type(e).__name__} - {e}", delete_after=10)
        else:
            self.save_loaded_extensions()
            await ctx.send(f"loaded {cog} successfully", delete_after=3)

    @commands.command()
    async def unload(self, ctx, cog: str) -> None:
        """Unload extension, eg. !unload image"""
        await ctx.message.delete()
        if self._prefix_cog(cog) == "cogs.admin":
            await ctx.send(
                "I'm afraid I can't let you do that", delete_after=3
            )
            return
        try:
            self.bot.unload_extension(self._prefix_cog(cog))
        except commands.ExtensionNotLoaded:
            await ctx.send("No such extension loaded", delete_after=3)
        except Exception as e:
            await ctx.send(f"Error: {type(e).__name__} - {e}", delete_after=10)
        else:
            self.save_loaded_extensions()
            await ctx.send(f"{cog} unloaded successfully", delete_after=3)

    @commands.command()
    async def reload(self, ctx, cog: str) -> None:
        """Reload extension, eg. !reload image"""
        await ctx.message.delete()
        try:
            self.bot.reload_extension(self._prefix_cog(cog))
        except commands.ExtensionNotLoaded:
            await ctx.send("No such extension loaded", delete_after=3)
        except Exception as e:
            await ctx.send(f"Error: {type(e).__name__} - {e}", delete_after=10)
        else:
            await ctx.send(f"{cog} reloaded successfully", delete_after=3)

    @commands.command()
    async def extensions(self, ctx) -> None:
        """Shows extensions available and loaded"""
        loaded = [self._strip_cog(e) for e in self.bot.extensions]
        available = self.enumerate_extensions()
        available = available - set(loaded)
        embed = discord.Embed()
        embed.add_field(name="Loaded", value=", ".join(loaded), inline=False)
        embed.add_field(
            name="Available", value=", ".join(available), inline=False
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx) -> None:
        """Ping!"""
        await ctx.message.delete()
        await ctx.send("pong!", delete_after=3)

    @commands.command(hidden=True)
    async def pong(self, ctx) -> None:
        await ctx.message.delete()
        await ctx.send("peng!", delete_after=3)

    @commands.command()
    async def clear(self, ctx, limit: Optional[int] = 100) -> None:
        """clear channel of bot messages,
        defaults to last 100 messages
        """
        async with ctx.channel.typing():
            for message in await ctx.channel.history(limit=limit).flatten():
                if message.author.id == self.bot.user.id:
                    await message.delete()
        await ctx.message.delete()
        await ctx.send("Messages cleared!", delete_after=3)

    @commands.command()
    async def quit(self, ctx) -> None:
        """Tells bot to quit"""
        await ctx.message.delete()
        message = await ctx.send("bye!")
        await asyncio.sleep(3)
        await message.delete()
        await self.bot.close()


def setup(bot):
    bot.add_cog(AdminCog(bot))
