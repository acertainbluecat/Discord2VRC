from typing import List
from fastapi import APIRouter, Query

from common.database import Mongo
from common.utils import Order, get_channel
from common.models import ChannelModel, ImageModel


router = APIRouter()


@router.get("/all/count", response_model=int)
async def all_count():
    return await Mongo.db.count(ImageModel)


@router.get("/all/items", response_model=List[ImageModel])
async def all_items(
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
    return images


@router.get("/{alias}/info", response_model=ChannelModel)
async def alias_info(alias: str):
    return await get_channel(alias)


@router.get("/{alias}/count", response_model=int)
async def channel_count(alias: str):
    channel = await get_channel(alias)
    count = await Mongo.db.count(ImageModel, ImageModel.channel == channel.id)
    return count


@router.get("/{alias}/items", response_model=List[ImageModel])
async def allias_items(
    alias: str,
    skip: int = Query(0, le=100),
    limit: int = Query(100, le=100),
    order: Order = Order.desc,
):
    channel = await get_channel(alias)
    images = await Mongo.db.find(
        ImageModel,
        ImageModel.channel == channel.id,
        sort=getattr(ImageModel.attachment_id, order.value)(),
        skip=skip,
        limit=limit,
    )
    return images
