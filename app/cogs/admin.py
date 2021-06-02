import discord
import asyncio

from discord.ext import commands

class AdminCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def load(self, ctx, cog: str):
        await ctx.message.delete()
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'Error: {type(e).__name__} - {e}', delete_after=10)
        else:
            await ctx.send(f'loaded {cog} successfully', delete_after=3)

    @commands.command()
    async def unload(self, ctx, cog: str):
        await ctx.message.delete()
        if cog == "cogs.admin":
            await ctx.send("I'm afraid I can't let you do that", delete_after=3)
            return
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'Error: {type(e).__name__} - {e}', delete_after=10)
        else:
            await ctx.send(f'{cog} unloaded successfully', delete_after=3)

    @commands.command()
    async def reload(self, ctx, cog: str):
        await ctx.message.delete()
        try:
            self.bot.reload_extension(cog)
        except Exception as e:
            await ctx.send(f'Error: {type(e).__name__} - {e}', delete_after=10)
        else:
            await ctx.send(f'{cog} reloaded successfully', delete_after=3)

    @commands.command()
    async def extensions(self, ctx):
        await ctx.send("Extensions loaded: " + ", ".join(self.bot.extensions.keys()), delete_after=5)

    @commands.command()
    async def ping(self, ctx):
        await ctx.message.delete()
        await ctx.send("pong!", delete_after=3)

    @commands.command()
    async def clear(self, ctx, limit: int = 100):
        for message in await ctx.channel.history(limit=limit).flatten():
            if message.author.id == self.bot.user.id:
                await message.delete()
        await ctx.message.delete()

    @commands.command()
    async def quit(self, ctx):
        await ctx.message.delete()
        message = await ctx.send("bye!")
        await asyncio.sleep(3)
        await message.delete()
        await self.bot.close()


def setup(bot):
    bot.add_cog(AdminCog(bot))
