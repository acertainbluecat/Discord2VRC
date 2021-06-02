import random
import asyncio
import uvicorn

from config import DB_CONF
from model import Channel, Image

from enum import Enum
from datetime import datetime
from urllib.parse import quote_plus

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from odmantic import AIOEngine
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

db: AIOEngine = None

placeholder = "/static/404.png"
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class Order(str, Enum):
    asc = "asc"
    desc = "desc"

@app.on_event("startup")
async def startup_event():
    # this is gross
    global db
    DB_CONF["password"] = quote_plus(DB_CONF["password"])
    client = AsyncIOMotorClient(
        "mongodb://{username}:{password}@{host}:{port}/{database_name}".format(**DB_CONF))
    db = AIOEngine(motor_client=client, database=DB_CONF["database_name"])

@app.get("/")
async def root():
    return {"Message": "Nothing to see here"}

# helper methods

async def get_channel(alias: str) -> Channel:
    channel = await db.find_one(Channel,
                                Channel.alias == alias)
    return channel

# API Endpoints

@app.get("/api/all/count")
async def all_count():
    count = await db.count(Image)
    return count

@app.get("/api/all/items")
async def all_items(skip: int = 0, limit: int = 100):
    images = await db.find(Image,
                           sort=Image.attachment_id.desc(),
                           skip=skip, limit=limit)
    return images

@app.get("/api/{alias}/info")
async def alias_info(alias: str):
    channel = await get_channel(alias)
    return channel

@app.get("/api/{alias}/count")
async def channel_count(alias: str):
    channel = await get_channel(alias)
    count = await db.count(Image,
                           Image.channel == channel.id)
    return count

@app.get("/api/{alias}/items")
async def alias_items(alias: str, skip: int = 0, limit: int = 100):
    channel = await get_channel(alias)
    images = await db.find(Image,
                           Image.channel == channel.id,
                           sort=Image.attachment_id.desc(),
                           skip=skip, limit=limit)
    return images

# Endpoints for VRChat

@app.get("/vrc/all/latest")
async def all_latest():
    image = await db.find_one(Image,
                              Image.deleted == False,
                              sort=Image.attachment_id.desc())
    if image is not None:
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/random")
async def all_random_image():
    images = db.get_collection(Image)
    result = await images.aggregate([{"$sample": {"size": 1}},
                                     {"$match": {"deleted": False}}]).to_list(length=1)
    if len(result) > 0:
        return RedirectResponse(url="/"+result[0]["filepath"])
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/randomsync")
async def all_random_sync(timer: int = 5, offset: int = 0):
    count = await db.count(Image, Image.deleted == False)
    if count > 0:
        seed = int(datetime.now().timestamp() / timer) - offset
        random.seed(seed)
        num = random.randint(0, count-1)
        images = await db.find(Image,
                               Image.deleted == False,
                               sort=Image.attachment_id.desc(),
                               skip=num, limit=1)
        return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/{order}/{n}")
async def all_desc(order: Order, n: int):
    images = await db.find(Image,
                           Image.deleted == False,
                           sort=getattr(Image.attachment_id, order.value)(),
                           skip=n, limit=1)
    if images is not None:
        return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/latest")
async def channel_latest(alias: str):
    channel = await get_channel(alias)
    if channel:
        image = await db.find_one(Image,
                                 (Image.deleted == False) & (Image.channel == channel.id),
                                 sort=Image.created_at.desc())
        if image is not None:
            return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/random")
async def channel_random_image(alias: str):
    channel = await get_channel(alias)
    if channel:
        images = db.get_collection(Image)
        # $sample size must be less than 5% of total doc size
        result = await images.aggregate([
            {"$sample": {"size": 1}},
            {"$match": {"channel": ObjectId(channel.id), "deleted": False}}
        ]).to_list(length=1)
        if len(result) > 0:
            return RedirectResponse(url="/"+result[0]["filepath"])
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/randomsync")
async def channel_random_sync(alias: str, timer: int = 5, offset: int = 0):
    channel = await get_channel(alias)
    if channel:
        count = await db.count(Image,
                               Image.deleted == False,
                               Image.channel == channel.id)
        if count > 0:
            seed = int(datetime.now().timestamp() / timer) - offset
            random.seed(seed)
            num = random.randint(0, count-1)
            images = await db.find(Image,
                                  (Image.deleted == False) & (Image.channel == channel.id),
                                  sort=Image.created_at.desc(),
                                  skip=num, limit=1)
            return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/{order}/{n}")
async def channel_desc(alias: str, order: Order, n: int):
    channel = await get_channel(alias)
    if channel:
        images = await db.find(Image,
                              (Image.deleted == False) & (Image.channel == channel.id),
                              sort=getattr(Image.attachment_id, order.value)(),
                              skip=n, limit=1)
        if images is not None:
            return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

if __name__ == "__main__":

    uvicorn.run("main:app", host="sternenklar.nyanpa.su", port=5000, reload=True)
