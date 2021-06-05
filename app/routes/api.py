from typing import List

from pydantic import BaseModel
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from common.database import Mongo
from common.utils import Order, get_channel, get_image
from common.models import ChannelModel, ImageModel


router = APIRouter()


class Error(BaseModel):
    error: str


def NoItemsFoundResponse():
    response = {"error": "No items found"}
    return JSONResponse(content=response, status_code=404)


@router.get(
    "/channel/all",
    response_model=List[ImageModel],
    responses={404: {"model": Error}},
)
async def get_all_items(
    skip: int = Query(0, le=100),
    limit: int = Query(100, le=100),
    order: Order = Order.desc,
):
    images = await Mongo.db.find(
        ImageModel,
        sort=getattr(ImageModel.attachment_id, order.value)(),
        skip=skip,
        limit=limit,
    )
    if images is not None:
        return images
    return NoItemsFoundResponse()


@router.get(
    "/channel/{alias}",
    response_model=List[ImageModel],
    responses={404: {"model": Error}},
)
async def get_alias_items(
    alias: str,
    skip: int = Query(0, le=100),
    limit: int = Query(100, le=100),
    order: Order = Order.desc,
):
    channel = await get_channel(alias)
    if channel is not None:
        images = await Mongo.db.find(
            ImageModel,
            ImageModel.channel == channel.id,
            sort=getattr(ImageModel.attachment_id, order.value)(),
            skip=skip,
            limit=limit,
        )
        return images
    return NoItemsFoundResponse()


@router.get("/channel/all/count", response_model=int)
async def get_all_count():
    return await Mongo.db.count(ImageModel)


@router.get(
    "/channel/{alias}/count",
    response_model=int,
    responses={404: {"model": Error}},
)
async def get_alias_count(alias: str):
    channel = await get_channel(alias)
    if channel is not None:
        return await Mongo.db.count(
            ImageModel, ImageModel.channel == channel.id
        )
    return NoItemsFoundResponse()


@router.get(
    "/channel/{alias}/info",
    response_model=ChannelModel,
    responses={404: {"model": Error}},
)
async def get_alias_info(alias: str):
    channel = await get_channel(alias)
    if channel is not None:
        return channel
    return NoItemsFoundResponse()


@router.get(
    "/image/{attachment_id}",
    response_model=ImageModel,
    responses={404: {"model": Error}},
)
async def get_image_info(attachment_id: int):
    image = await get_image(attachment_id)
    if image is not None:
        return image
    return NoItemsFoundResponse()
