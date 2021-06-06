import random
from os import path

from bson.objectid import ObjectId
from fastapi import APIRouter, Query, Path
from starlette.responses import RedirectResponse, Response

from common.database import Mongo
from common.models import ImageModel
from common.utils import Order, get_channel, get_seed

router = APIRouter(default_response_class=Response)


def RedirectPlaceholder() -> RedirectResponse:
    return RedirectResponse(url="/placeholder.png")


def RedirectImage(filepath: str) -> RedirectResponse:
    return RedirectResponse(url=path.join("/", filepath))


@router.get("/all/latest")
async def all_latest():
    """Returns the latest image available"""
    image = await Mongo.db.find_one(
        ImageModel,
        ImageModel.deleted == False,
        sort=ImageModel.attachment_id.desc(),
    )
    if image is not None:
        return RedirectImage(image.filepath)
    return RedirectPlaceholder()


@router.get("/{alias}/latest")
async def channel_latest(alias: str):
    """Returns the latest image available from specified channel alias"""
    channel = await get_channel(alias)
    if channel:
        image = await Mongo.db.find_one(
            ImageModel,
            (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
            sort=ImageModel.created_at.desc(),
        )
        if image is not None:
            return RedirectImage(image.filepath)
    return RedirectPlaceholder()


@router.get("/all/random")
async def all_random_image():
    """Returns a random image"""
    images = Mongo.db.get_collection(ImageModel)
    result = await images.aggregate(
        [{"$sample": {"size": 1}}, {"$match": {"deleted": False}}]
    ).to_list(length=1)
    if result:
        return RedirectImage(result[0]["filepath"])
    return RedirectPlaceholder()


@router.get("/{alias}/random")
async def channel_random_image(alias: str):
    """Returns a random image from specified channel alias"""
    channel = await get_channel(alias)
    if channel:
        images = Mongo.db.get_collection(ImageModel)
        # $sample size must be less than 5% of total doc size
        result = await images.aggregate(
            [
                {"$sample": {"size": 1}},
                {
                    "$match": {
                        "channel": ObjectId(channel.id),
                        "deleted": False,
                    }
                },
            ]
        ).to_list(length=1)
        if result:
            return RedirectImage(result[0]["filepath"])
    return RedirectPlaceholder()


@router.get("/all/randomsync")
async def all_random_sync(interval: int = Query(5, ge=5), offset: int = 0):
    """Returns a random image that is pseudo synced for all requests
    based on interval and offset
    """
    count = await Mongo.db.count(ImageModel, ImageModel.deleted == False)
    if count > 0:
        random.seed(get_seed(interval, offset))
        num = random.randint(0, count - 1)
        images = await Mongo.db.find(
            ImageModel,
            ImageModel.deleted == False,
            sort=ImageModel.attachment_id.desc(),
            skip=num,
            limit=1,
        )
        return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()


@router.get("/{alias}/randomsync")
async def channel_random_sync(
    alias: str, interval: int = Query(5, ge=5), offset: int = 0
):
    """Returns a random image that is pseudo synced for all requests
    based on interval and offset, from the specified channel alias
    """
    channel = await get_channel(alias)
    if channel:
        count = await Mongo.db.count(
            ImageModel,
            ImageModel.deleted == False,
            ImageModel.channel == channel.id,
        )
        if count > 0:
            random.seed(get_seed(interval, offset))
            num = random.randint(0, count - 1)
            images = await Mongo.db.find(
                ImageModel,
                (ImageModel.deleted == False)
                & (ImageModel.channel == channel.id),
                sort=ImageModel.created_at.desc(),
                skip=num,
                limit=1,
            )
            return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()


@router.get("/all/{order}/{n}")
async def all_ordered(order: Order, n: int = Path(..., ge=0)):
    """Returns the n'th image in asc/desc order from discord channel
    messages"""
    images = await Mongo.db.find(
        ImageModel,
        ImageModel.deleted == False,
        sort=getattr(ImageModel.attachment_id, order.value)(),
        skip=n,
        limit=1,
    )
    if images is not None:
        return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()


@router.get("/{alias}/{order}/{n}")
async def channel_ordered(alias: str, order: Order, n: int = Path(..., ge=0)):
    """Returns the n'th image in asc/desc order from discord channel messages
    from specified channel alias
    """
    channel = await get_channel(alias)
    if channel:
        images = await Mongo.db.find(
            ImageModel,
            (ImageModel.deleted == False) & (ImageModel.channel == channel.id),
            sort=getattr(ImageModel.attachment_id, order.value)(),
            skip=n,
            limit=1,
        )
        if images is not None:
            return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()
