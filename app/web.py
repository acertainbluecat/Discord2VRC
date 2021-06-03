import random
import asyncio
import uvicorn

from common.config import DB_CONF
from common.models import ChannelModel, ImageModel

from enum import Enum
from datetime import datetime
from urllib.parse import quote_plus

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from odmantic import AIOEngine
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

DB: AIOEngine = None

placeholder = "/static/404.png"
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class Order(str, Enum):
    asc = "asc"
    desc = "desc"

@app.on_event("startup")
async def startup_event():
    # this is gross
    global DB
    DB_CONF["password"] = quote_plus(DB_CONF["password"])
    client = AsyncIOMotorClient(
        "mongodb://{username}:{password}@{host}:{port}/{database_name}".format(**DB_CONF))
    DB = AIOEngine(motor_client=client, database=DB_CONF["database_name"])

@app.get("/")
async def root():
    return {"Message": "Nothing to see here"}

# helper methods

async def get_channel(alias: str) -> ChannelModel:
    channel = await DB.find_one(ChannelModel,
                                ChannelModel.alias == alias)
    return channel

# API Endpoints

@app.get("/api/all/count")
async def all_count():
    count = await DB.count(ImageModel)
    return count

@app.get("/api/all/items")
async def all_items(skip: int = 0, limit: int = 100):
    images = await DB.find(ImageModel,
                           sort=ImageModel.attachment_id.desc(),
                           skip=skip, limit=limit)
    return images

@app.get("/api/{alias}/info")
async def alias_info(alias: str):
    channel = await get_channel(alias)
    return channel

@app.get("/api/{alias}/count")
async def channel_count(alias: str):
    channel = await get_channel(alias)
    count = await DB.count(ImageModel,
                           ImageModel.channel == channel.id)
    return count

@app.get("/api/{alias}/items")
async def alias_items(alias: str, skip: int = 0, limit: int = 100):
    channel = await get_channel(alias)
    images = await DB.find(ImageModel,
                           ImageModel.channel == channel.id,
                           sort=ImageModel.attachment_id.desc(),
                           skip=skip, limit=limit)
    return images

# Endpoints for VRChat

@app.get("/vrc/all/latest")
async def all_latest():
    image = await DB.find_one(ImageModel,
                              ImageModel.deleted == False,
                              sort=ImageModel.attachment_id.desc())
    if image is not None:
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/random")
async def all_random_image():
    images = DB.get_collection(ImageModel)
    result = await images.aggregate([{"$sample": {"size": 1}},
                                     {"$match": {"deleted": False}}]).to_list(length=1)
    if len(result) > 0:
        return RedirectResponse(url="/"+result[0]["filepath"])
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/randomsync")
async def all_random_sync(interval: int = 5, offset: int = 0):
    count = await DB.count(ImageModel, ImageModel.deleted == False)
    if count > 0:
        seed = int(datetime.now().timestamp() / interval) - (offset * 1000)
        random.seed(seed)
        num = random.randint(0, count-1)
        images = await DB.find(ImageModel,
                               ImageModel.deleted == False,
                               sort=ImageModel.attachment_id.desc(),
                               skip=num, limit=1)
        return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/{order}/{n}")
async def all_desc(order: Order, n: int):
    images = await DB.find(ImageModel,
                           ImageModel.deleted == False,
                           sort=getattr(ImageModel.attachment_id, order.value)(),
                           skip=n, limit=1)
    if images is not None:
        return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/latest")
async def channel_latest(alias: str):
    channel = await get_channel(alias)
    if channel:
        image = await DB.find_one(ImageModel,
                                 (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
                                 sort=ImageModel.created_at.desc())
        if image is not None:
            return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/random")
async def channel_random_image(alias: str):
    channel = await get_channel(alias)
    if channel:
        images = DB.get_collection(ImageModel)
        # $sample size must be less than 5% of total doc size
        result = await images.aggregate([
            {"$sample": {"size": 1}},
            {"$match": {"channel": ObjectId(channel.id), "deleted": False}}
        ]).to_list(length=1)
        if len(result) > 0:
            return RedirectResponse(url="/"+result[0]["filepath"])
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/randomsync")
async def channel_random_sync(alias: str, interval: int = 5, offset: int = 0):
    channel = await get_channel(alias)
    if channel:
        count = await DB.count(ImageModel,
                               ImageModel.deleted == False,
                               ImageModel.channel == channel.id)
        if count > 0:
            seed = int(datetime.now().timestamp() / interval) - (offset * 1000)
            random.seed(seed)
            num = random.randint(0, count-1)
            images = await DB.find(ImageModel,
                                  (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
                                  sort=ImageModel.created_at.desc(),
                                  skip=num, limit=1)
            return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{alias}/{order}/{n}")
async def channel_desc(alias: str, order: Order, n: int):
    channel = await get_channel(alias)
    if channel:
        images = await DB.find(ImageModel,
                              (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
                              sort=getattr(ImageModel.attachment_id, order.value)(),
                              skip=n, limit=1)
        if images is not None:
            return RedirectResponse(url="/"+images[0].filepath)
    return RedirectResponse(url=placeholder)

if __name__ == "__main__":

    uvicorn.run("web:app", host="sternenklar.nyanpa.su", port=5000, reload=True)
