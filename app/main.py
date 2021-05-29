import asyncio
import uvicorn

from model import Image
from config import DB_CONF
from urllib.parse import quote_plus

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

db: AIOEngine = None

placeholder = "/static/404.png"
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    # this is gross
    global db
    DB_CONF["password"] = quote_plus(DB_CONF["password"])
    client = AsyncIOMotorClient("mongodb://{username}:{password}@{host}:{port}/{database_name}".format(**DB_CONF))
    db = AIOEngine(motor_client=client, database=DB_CONF["database_name"])

@app.get("/")
async def root():
    return {"Message": "Nothing to see here"}

@app.get("/api/all/count")
async def count():
    count = await db.count(Image)
    return count

@app.get("/api/{channel}/count")
async def count(channel: str):
    count = await db.count(Image.channel == channel)
    return count

@app.get("/vrc/all/latest")
async def latest():
    image = await db.find_one(Image, sort = Image.created_at.desc())
    if image is not None:
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/random")
async def random():
    images = db.get_collection(Image)
    result = await images.aggregate([{"$sample": { "size": 1 }}]).to_list(length=1)
    image = Image.parse_doc(result[0])
    if len(result) is not 0:
        image = Image.parse_doc(result[0])
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/desc/{n}")
async def desc(n: int):
    images = await db.find(Image, sort = Image.created_at.desc())
    if images is not None and len(images) > n:
        image = images[n]
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/all/asc/{n}")
async def asc(n: int):
    images = await db.find(Image, sort = Image.created_at.asc())
    if images is not None and len(images) > n:
        image = images[n]
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{channel}/latest")
async def latest(channel: str):
    image = await db.find_one(Image, Image.channel == channel, sort = Image.created_at.desc())
    if image is not None:
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{channel}/random")
async def random(channel: str):
    images = db.get_collection(Image)
    result = await images.aggregate([
        {"$sample": { "size": 1 }},
        {"$match": {"channel": channel}}
    ]).to_list(length=1)
    if len(result) is not 0:
        image = Image.parse_doc(result[0])
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{channel}/desc/{n}")
async def desc(channel: str, n: int):
    images = await db.find(Image, Image.channel == channel, sort = Image.created_at.desc())
    if images is not None and len(images) > n:
        image = images[n]
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

@app.get("/vrc/{channel}/asc/{n}")
async def asc(channel: str, n: int):
    images = await db.find(Image, Image.channel == channel, sort = Image.created_at.asc())
    if images is not None and len(images) > n:
        image = images[n]
        return RedirectResponse(url="/"+image.filepath)
    return RedirectResponse(url=placeholder)

if __name__ == "__main__":

    uvicorn.run(app, host="localhost", port=5000)
