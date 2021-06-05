import io
import discord
import asyncio

from os import path
from PIL import Image
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

    async def _load_channels(self):
        self.channels = {
            c.channel_id: c async for c in Mongo.db.find(ChannelModel)
        }

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
        image = await Mongo.db.find_one(
            ImageModel, ImageModel.attachment_id == attachment.id
        )
        if image is not None:
            image.deleted = False
            await Mongo.db.save(image)
            return True
        return False

    async def _alias_exists(self, alias: str) -> bool:
        channel = await Mongo.db.find_one(
            ChannelModel, ChannelModel.alias == alias
        )
        if channel is not None:
            return True
        return False

    async def _save_image(self, image_bytes: bytes, filepath: str):
        im = Image.open(io.BytesIO(image_bytes))
        im_jpg = im.convert("RGB")
        im_jpg.save(filepath, quality=80)

    async def _handle_upload(
        self, message: discord.Message, attachment: discord.Attachment
    ) -> bool:
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

    async def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        return await self.bot.is_owner(ctx.author)

    def is_subscribed(self, ctx) -> bool:
        if ctx.channel.id not in self.channels.keys():
            return False
        return self.channels[ctx.channel.id].subscribed

    def was_subscribed(self, ctx) -> bool:
        return ctx.channel.id in self.channels.keys()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return
        if message.channel.id not in self.channels.keys():
            return
        if await self._has_attachments(message):
            await self._handle_attachments(message)

    @commands.command()
    async def rescan(self, ctx, limit: int = 100):
        """Rescans current channel for images if it is subscribed"""
        if not self.is_subscribed(ctx):
            return
        uploaded = 0
        messages = await ctx.channel.history(limit=limit + 1).flatten()
        await ctx.message.delete()
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
    async def subscribe(self, ctx, alias: str = None):
        """Subscribe current channel for image crawling"""
        await ctx.message.delete()
        if self.is_subscribed(ctx):
            await ctx.send(
                "This channel is already subscribed!", delete_after=3
            )
            return
        if alias is None:
            alias = ctx.channel.name
        if await self._alias_exists(alias):
            await ctx.send(
                f"The alias \"{alias}\" already exists, please pick another",
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
            f"This channel is now subscribed with alias \"{alias}\"",
            delete_after=3,
        )

    @commands.command()
    async def unsubscribe(self, ctx):
        """Unsubscribe current channel for image crawling"""
        await ctx.message.delete()
        if self.is_subscribed(ctx):
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
    async def alias(self, ctx, alias: str = None):
        """Sets an alias for current channel's subscription"""
        if not self.is_subscribed(ctx):
            return
        await ctx.message.delete()
        if alias is None:
            await ctx.send(
                f"This channel's alias is"
                f"\"{self.channels[ctx.channel.id].alias}\"",
                delete_after=3,
            )
            return
        if await self._alias_exists(alias):
            await ctx.send(
                f"The alias \"{alias}\" already exists, please pick another",
                delete_after=3,
            )
            return
        channel = self.channels[ctx.channel.id]
        channel.alias = alias
        await Mongo.db.save(channel)
        await ctx.send(
            f"This channel's alias has been changed to \"{alias}\"",
            delete_after=3,
        )

    @commands.command()
    async def status(self, ctx):
        """Shows current channels subscription status"""
        await ctx.message.delete()
        if not self.is_subscribed(ctx):
            await ctx.send("This channel is not subscribed", delete_after=3)
            return
        channel = self.channels[ctx.channel.id]
        count = await Mongo.db.count(
            ImageModel,
            (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
        )
        await ctx.send(
            f"There are currently {count} images from this channel "
            f"indexed under the alias \"{channel.alias}\"",
            delete_after=5,
        )

    @commands.command()
    async def purge(self, ctx):
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
    async def reactclear(self, ctx, limit: int = 100):
        """Clear all bot reactions from this channel"""
        await ctx.message.delete()
        msg = await ctx.send(
            f"Clearing my reactions from the last {limit} messages"
        )
        for message in await ctx.channel.history(limit=limit).flatten():
            for reaction in message.reactions:
                if reaction.me:
                    await reaction.remove(self.bot.user)
        await msg.delete()


def setup(bot):
    bot.add_cog(ImageCog(bot))
