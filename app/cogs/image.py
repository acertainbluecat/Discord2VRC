import discord
import asyncio

from os import path
from discord.ext import commands

from model import Image
from config import BOT_CONF, UPLOAD_DIRECTORY

class ImageCog(commands.Cog):

    exts = [".jpg", ".jpeg", ".png"]
    emoji = {"success": "✅", "loading": "⌛"}

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_image(self, attachment: discord.Attachment) -> bool:
        for ext in self.exts:
            if attachment.filename.endswith(ext):
                return True
        return False

    async def _has_attachments(self, message: discord.Message) -> bool:
        if len(message.attachments) > 0:
            return True
        return False

    async def _handle_attachments(self, message: discord.Message) -> int:
        uploaded, exists = 0, 0
        await message.add_reaction(self.emoji["loading"])
        for attachment in message.attachments:
            if await self._is_image(attachment):
                if await self._upload_exists(attachment):
                    exists += 1
                elif await self._handle_upload(message, attachment):
                    uploaded += 1
        if uploaded > 0 or exists > 0:
            await message.add_reaction(self.emoji["success"])
        await message.remove_reaction(self.emoji["loading"], self.bot.user)
        return uploaded

    async def _upload_exists(self, attachment: discord.Attachment) -> bool:
        image = await self.bot.db.find_one(Image, Image.attachment_id == attachment.id)
        if image is not None:
            return True
        return False

    async def _handle_upload(self, message: discord.Message, attachment: discord.Attachment) -> bool:
        try:
            ext = path.splitext(attachment.filename)[1]
            filepath = path.join(UPLOAD_DIRECTORY, str(attachment.id) + ext)
            await attachment.save(filepath)
        except discord.HTTPException:
            await message.reply(f"HTTPException when attempting to download image {attachment.id}")
        except discord.NotFound:
            await message.channel.send(f"NotFound exception when attempting to download image {attachment.id}")
        else:
            image = Image(
                filename = attachment.filename,
                filepath = filepath,
                attachment_id = attachment.id,
                guild = message.guild.name,
                guild_id = message.guild.id,
                channel = message.channel.name,
                channel_id = message.channel.id,
                username = message.author.name,
                user_num = message.author.discriminator,
                user_id = message.author.id,
                message_id = message.id
            )
            await self.bot.db.save(image)
            return True
        return False

    async def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        is_owner = await self.bot.is_owner(ctx.author)
        is_valid_channel = ctx.channel.id in self.bot.valid_channels
        return is_owner and is_valid_channel

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return
        if message.channel.id not in BOT_CONF["channel_ids"]:
            return
        if await self._has_attachments(message):
            await self._handle_attachments(message)

    @commands.command()
    async def rescan(self, ctx, limit: int = 100):
        if ctx.message.channel.id not in BOT_CONF["channel_ids"]:
            return

        uploaded = 0
        await ctx.message.delete()
        response = await ctx.send(f"Rescanning the last {limit} messages for images")
        messages = await ctx.channel.history(limit=limit+1).flatten()
        for message in messages[::-1]:
            if await self._has_attachments(message):
                uploaded += await self._handle_attachments(message)
        await response.delete()
        await ctx.send(f"Rescan complete, added {uploaded} images", delete_after = 3)

    @commands.command()
    async def clear(self, ctx, limit: int = 100):
        async for message in ctx.channel.history(limit = limit):
            if message.author.id == self.bot.user.id:
                await message.delete()
            for reaction in message.reactions:
                if reaction.me:
                    await reaction.remove(self.bot.user)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(ImageCog(bot))
