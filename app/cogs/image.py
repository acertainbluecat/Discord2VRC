import io
import discord
import asyncio

from os import path
from PIL import Image
from typing import Optional
from discord.ext import commands

from common.config import config
from common.database import Mongo
from common.models import ChannelModel, ImageModel


class ImageCog(commands.Cog, name="Image"):
    """This extension handles the crawling and management of images"""

    exts = [".jpg", ".jpeg", ".png"]
    emoji = {"success": "✅", "loading": "⌛"}

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.ensure_future(self._load_channels())

    async def _load_channels(self) -> None:
        """Loads channels bot is listening to for images"""
        self.channels = {
            int(c.channel_id): c async for c in Mongo.db.find(ChannelModel)
        }

    async def _is_image(self, attachment: discord.Attachment) -> bool:
        """Check if attachment is an image based on exts"""
        for ext in self.exts:
            if attachment.filename.endswith(ext):
                return True
        return False

    async def _has_attachments(self, message: discord.Message) -> bool:
        """Check if message has attachments"""
        if len(message.attachments) > 0:
            return True
        return False

    async def _handle_attachments(self, message: discord.Message) -> int:
        """Handle processing of attachments for images"""
        uploaded = 0
        await message.add_reaction(self.emoji["loading"])
        for attachment in message.attachments:
            if await self._is_image(attachment):
                if await self._upload_exists(attachment):
                    uploaded += 1
                elif await self._handle_upload(message, attachment):
                    uploaded += 1
        if uploaded > 0:
            await message.add_reaction(self.emoji["success"])
        await message.remove_reaction(self.emoji["loading"], self.bot.user)
        return uploaded

    async def _upload_exists(self, attachment: discord.Attachment) -> bool:
        """Check if image in attachment has already been uploaded"""
        image = await Mongo.db.find_one(
            ImageModel, ImageModel.attachment_id == str(attachment.id)
        )
        if image is not None:
            image.deleted = False
            await Mongo.db.save(image)
            return True
        return False

    async def _alias_exists(self, alias: str) -> bool:
        """Check if channel alias already exists"""
        channel = await Mongo.db.find_one(
            ChannelModel, ChannelModel.alias == alias
        )
        if channel is not None:
            return True
        return False

    async def _save_image(self, image_bytes: bytes, filepath: str) -> None:
        """Converts image to jpg with q=80 and saves to disk"""
        im = Image.open(io.BytesIO(image_bytes))
        im_jpg = im.convert("RGB")
        im_jpg.save(filepath, quality=80)

    async def _handle_upload(
        self, message: discord.Message, attachment: discord.Attachment
    ) -> bool:
        """Handles the upload of image attachments"""
        try:
            filename = str(attachment.id) + ".jpg"
            filepath = path.join(config["directories"]["uploadsdir"], filename)
            relative_uri = path.join(
                config["directories"]["uploadsfolder"], filename
            )
            image_bytes = await attachment.read()
            await self._save_image(image_bytes, filepath)
        except discord.HTTPException:
            await message.reply(f"Error downloading image: {attachment.id}")
        except discord.NotFound:
            await message.channel.send(
                f"Attachment not found: {attachment.id}"
            )
        else:
            image = ImageModel(
                filename=attachment.filename,
                filepath=relative_uri,
                attachment_id=attachment.id,
                username=message.author.name,
                user_num=message.author.discriminator,
                user_id=message.author.id,
                message_id=message.id,
                created_at=message.created_at,
                channel=self.channels[message.channel.id],
            )
            await Mongo.db.save(image)
            return True
        return False

    async def cog_check(self, ctx) -> bool:
        """Discord cog check function"""
        if ctx.guild is None:
            return False
        return await self.bot.is_owner(ctx.author)

    def is_subscribed(self, channel_id: int) -> bool:
        """Checks if channel is subscribed for images"""
        if channel_id in self.channels.keys():
            return self.channels[channel_id].subscribed
        return False

    def was_subscribed(self, ctx) -> bool:
        """Checks if channel was subscribed for images"""
        return ctx.channel.id in self.channels.keys()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Reads every message in subscribed channels for images"""
        if message.author.id == self.bot.user.id:
            return
        if self.is_subscribed(message.channel.id):
            if await self._has_attachments(message):
                await self._handle_attachments(message)

    @commands.command()
    async def rescan(self, ctx, limit: int = 100) -> None:
        """Rescans current channel for images if it is subscribed"""
        await ctx.message.delete()
        if not self.is_subscribed(ctx.channel.id):
            await ctx.send("This channel is not subscribed!", delete_after=3)
            return
        async with ctx.channel.typing():
            uploaded = 0
            messages = await ctx.channel.history(limit=limit + 1).flatten()
            count = len(messages)
            response = await ctx.send(
                f"Rescanning the last {count} messages for images"
            )
            current = 0
            progress = await ctx.send(content=f"Progress {current}/{count}")
            for message in messages[::-1]:
                if await self._has_attachments(message):
                    uploaded += await self._handle_attachments(message)
                current += 1
                await progress.edit(content=f"Progress {current}/{count}")
            await response.delete()
            await progress.delete()
        await ctx.send(
            f"Rescan complete, added {uploaded} new images", delete_after=3
        )

    @commands.command()
    async def subscribe(self, ctx, alias: Optional[str] = None) -> None:
        """Subscribe current channel for image crawling"""
        await ctx.message.delete()
        if self.is_subscribed(ctx.channel.id):
            await ctx.send(
                "This channel is already subscribed!", delete_after=3
            )
            return
        if alias is None:
            alias = ctx.channel.name
        if await self._alias_exists(alias):
            await ctx.send(
                f'The alias "{alias}" already exists, please pick another',
                delete_after=3,
            )
            return
        if self.was_subscribed(ctx):
            channel = self.channels[ctx.channel.id]
            channel.alias = alias
            channel.subscribed = True
            await Mongo.db.save(channel)
        else:
            channel = ChannelModel(
                channel_id=ctx.channel.id,
                channel_name=ctx.channel.name,
                alias=alias,
                guild=ctx.guild.name,
                guild_id=ctx.guild.id,
            )
            await Mongo.db.save(channel)
        await self._load_channels()
        await ctx.send(
            f'This channel is now subscribed with alias "{alias}"',
            delete_after=3,
        )

    @commands.command()
    async def unsubscribe(self, ctx) -> None:
        """Unsubscribe current channel for image crawling"""
        await ctx.message.delete()
        if self.is_subscribed(ctx.channel.id):
            channel = self.channels[ctx.channel.id]
            channel.subscribed = False
            channel.alias = str(channel.id)
            await Mongo.db.save(channel)
            await self._load_channels()
            await ctx.send(
                "This channel has been unsubscribed!", delete_after=3
            )
        else:
            await ctx.send("This channel is not subscribed!", delete_after=3)
            return

    @commands.command()
    async def alias(self, ctx, alias: Optional[str] = None) -> None:
        """Sets an alias for current channel's subscription"""
        if not self.is_subscribed(ctx.channel.id):
            return
        await ctx.message.delete()
        if alias is None:
            await ctx.send(
                f"This channel's alias is"
                f'"{self.channels[ctx.channel.id].alias}"',
                delete_after=3,
            )
            return
        if await self._alias_exists(alias):
            await ctx.send(
                f'The alias "{alias}" already exists, please pick another',
                delete_after=3,
            )
            return
        channel = self.channels[ctx.channel.id]
        channel.alias = alias
        await Mongo.db.save(channel)
        await ctx.send(
            f'This channel\'s alias has been changed to "{alias}"',
            delete_after=3,
        )

    @commands.command()
    async def status(self, ctx) -> None:
        """Shows current channels subscription status"""
        await ctx.message.delete()
        if not self.is_subscribed(ctx.channel.id):
            await ctx.send("This channel is not subscribed", delete_after=3)
            return
        channel = self.channels[ctx.channel.id]
        count = await Mongo.db.count(
            ImageModel,
            (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
        )
        await ctx.send(
            f"There are currently {count} images from this channel "
            f'indexed under the alias "{channel.alias}"',
            delete_after=5,
        )

    @commands.command()
    async def purge(self, ctx) -> None:
        """Soft deletes all images downloaded from this channel"""
        if not self.was_subscribed(ctx):
            return
        await ctx.message.delete()
        channel = self.channels[ctx.channel.id]
        images = await Mongo.db.find(
            ImageModel,
            (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
        )
        for image in images:
            image.deleted = True
        await Mongo.db.save_all(images)
        await ctx.send(
            f"{len(images)} images from this channel have been purged",
            delete_after=3,
        )

    @commands.command()
    async def reactclear(self, ctx, limit: Optional[int] = 100) -> None:
        """Clear bot reactions from this channel,
        defaults to last 100 messages
        """
        async with ctx.channel.typing():
            for message in await ctx.channel.history(limit=limit).flatten():
                for reaction in message.reactions:
                    if reaction.me:
                        await reaction.remove(self.bot.user)
        await ctx.message.delete()
        await ctx.send("Reactions cleared!", delete_after=3)


def setup(bot):
    bot.add_cog(ImageCog(bot))
