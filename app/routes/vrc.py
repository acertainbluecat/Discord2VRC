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


@router.get("/all/image/{index}")
async def all_ordered(
    index: int = Path(..., ge=0),
    order: Order = Order.desc,
):
    """Returns the image based on the index provided and order specified.
    Defaults to decending order
    """
    images = await Mongo.db.find(
        ImageModel,
        ImageModel.deleted == False,
        sort=getattr(ImageModel.attachment_id, order.value)(),
        skip=index,
        limit=1,
    )
    if images is not None:
        return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()


@router.get("/all/random")
async def all_random_image():
    """Returns a random image"""
    images = Mongo.db.get_collection(ImageModel)
    result = await images.aggregate(
        [{"$match": {"deleted": False}}, {"$sample": {"size": 1}}]
    ).to_list(length=1)
    if result:
        return RedirectImage(result[0]["filepath"])
    return RedirectPlaceholder()


@router.get("/all/randomsync")
async def all_random_sync(
    interval: int = Query(5, ge=5),
    offset: int = 0,
):
    """Returns a random image that is pseudo synced for all requests
    based on interval and offset for a seeded rng
    """
    count = await Mongo.db.count(ImageModel, ImageModel.deleted == False)
    if count > 0:
        random.seed(get_seed(interval, offset))
        num = random.randint(0, count - 1)
        images = await Mongo.db.find(
            ImageModel,
            ImageModel.deleted == False,
            sort=ImageModel.attachment_id.desc(),  # type: ignore[attr-defined]
            skip=num,
            limit=1,
        )
        return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()


@router.get("/channel/{alias}/image/{index}")
async def channel_ordered(
    alias: str,
    index: int = Path(..., ge=0),
    order: Order = Order.desc,
):
    """Returns the image based on the index provided and order specified,
    and Channel alias. Defaults to decending order
    """
    channel = await get_channel(alias)
    if channel is not None:
        images = await Mongo.db.find(
            ImageModel,
            ImageModel.deleted == False,
            ImageModel.channel == channel.id,
            sort=getattr(ImageModel.attachment_id, order.value)(),
            skip=index,
            limit=1,
        )
        if images is not None:
            return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()


@router.get("/channel/{alias}/random")
async def channel_random_image(alias: str):
    """Returns a random image from specified channel alias."""
    channel = await get_channel(alias)
    if channel is not None:
        images = Mongo.db.get_collection(ImageModel)
        result = await images.aggregate(
            [
                {
                    "$match": {
                        "channel": ObjectId(channel.id),
                        "deleted": False,
                    }
                },
                {"$sample": {"size": 1}},
            ]
        ).to_list(length=1)
        if result:
            return RedirectImage(result[0]["filepath"])
    return RedirectPlaceholder()


@router.get("/channel/{alias}/randomsync")
async def channel_random_sync(
    alias: str,
    interval: int = Query(5, ge=5),
    offset: int = 0,
):
    """Returns a random image that is pseudo synced for all requests
    based on interval and offset for a seeded rng,
    from the specified channel alias
    """
    channel = await get_channel(alias)
    if channel is not None:
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
                ImageModel.deleted == False,
                ImageModel.channel == channel.id,
                sort=ImageModel.created_at.desc(),  # type: ignore[attr-defined]
                skip=num,
                limit=1,
            )
            return RedirectImage(images[0].filepath)
    return RedirectPlaceholder()
