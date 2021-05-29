import discord
import asyncio

from os import path
from discord.ext import commands
from urllib.parse import quote_plus

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from model import Image
from config import DB_CONF, BOT_CONF, UPLOAD_DIRECTORY

def init_db(config):
    config["password"] = quote_plus(config["password"])
    client = AsyncIOMotorClient("mongodb://{username}:{password}@{host}:{port}/{database_name}".format(**config))
    return AIOEngine(motor_client=client, database=config["database_name"])

description = '''A bot that saves images from discord to display in vrchat'''
bot = commands.Bot(command_prefix='!', description=description)
db = init_db(DB_CONF)
exts = [".jpg", ".jpeg", ".png"]
emoji_success = "✅"

@bot.event
async def on_ready():
    print('Logged on as', bot.user)

@bot.event
async def on_command_error(ctx, error):
    await ctx.message.delete()
    message = await ctx.send(f"Unknown command!")
    await asyncio.sleep(3)
    await message.delete()

@bot.command()
async def ping(ctx):
    message = await ctx.send("pong!")
    await ctx.message.delete()
    await asyncio.sleep(3)
    await message.delete()

@bot.command()
async def rescan(ctx, limit: int = 100):
    if ctx.message.channel.id not in BOT_CONF["channel_ids"]:
        return

    count = 0
    await ctx.message.delete()
    response = await ctx.send(f"Rescanning the last {limit} messages for images")
    async for message in ctx.channel.history(limit=limit + 2):
        count += 1 if await check_attachments(message) else 0
    await response.delete()
    response = await ctx.send(f"Rescan complete, added {count} images")
    await asyncio.sleep(3)
    await response.delete()

@bot.command()
async def clear(ctx, limit: int = 100):
    async for message in ctx.channel.history(limit=limit):
        if message.author.id == bot.user.id:
            await message.delete()
        for reaction in message.reactions:
            if reaction.me:
                await reaction.remove(bot.user)
    await ctx.message.delete()

@bot.listen('on_message')
async def listen_attachments(message):
    if message.author.id == bot.user.id:
        return
    if message.channel.id not in BOT_CONF["channel_ids"]:
        return
    await check_attachments(message)

"""
async def authorized(message):
    if message.author.id in BOT_CONF["authorized"]:
        return True
    return False

async def not_authorized(ctx):
    ctx.message.delete()
    await response = ctx.send("You are not authorized to use bot commands")
    asyncio.sleep(3)
    await response.delete()
"""

async def has_attachments(message) -> bool:
    if len(message.attachments) > 0:
        return True
    return False

async def check_attachments(message) -> bool:
    for attachment in message.attachments:
        for ext in exts:
            if attachment.filename.endswith(ext):
                return await handle_upload(message, attachment, ext)

async def upload_exists(attachment) -> bool:
    image = await db.find_one(Image, Image.attachment_id == attachment.id)
    if image is not None:
        return True
    return False

async def handle_upload(message, attachment, ext) -> bool:
    uploaded = False
    if await upload_exists(attachment):
        await message.add_reaction(emoji_success)
        return uploaded

    try:
        filepath = path.join(UPLOAD_DIRECTORY, str(attachment.id) + ext)
        await attachment.save(filepath)
    except discord.HTTPException:
        await message.reply("HTTPException when attempting to download image")
    except discord.NotFound:
        await message.channel.send("NotFound exception when attempting to download image")
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
            user_id = message.author.id
        )
        await db.save(image)
        await message.add_reaction(emoji_success)
        uploaded = True
    finally:
        return uploaded

if __name__ == "__main__":

    bot.run(BOT_CONF["token"])
