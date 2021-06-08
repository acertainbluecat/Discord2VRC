from typing import List, Optional

from pydantic import BaseModel
from odmantic.query import QueryExpression
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from common.database import Mongo
from common.utils import Order, get_channel, get_image
from common.models import ChannelModel, ImageModel


router = APIRouter()


class NotFoundError(BaseModel):
    error: str = "Not found"


def NotFoundResponse(message: str = "Not found"):
    response = NotFoundError(error=message)
    return JSONResponse(content=response.dict(), status_code=404)


@router.get(
    "/image",
    response_model=List[ImageModel],
    responses={404: {"model": NotFoundError}},
)
async def get_images(
    alias: Optional[str] = None,
    skip: Optional[int] = Query(0, ge=0, le=100),
    limit: Optional[int] = Query(100, ge=0, le=100),
    order: Optional[Order] = Order.desc,
    deleted: Optional[bool] = None,
):
    """Retrieves image documents, if alias is not provided
    will retrieve all images.
    """
    queries: List[QueryExpression] = []
    options = {
        "sort": getattr(ImageModel.attachment_id, order.value)(),
        "skip": skip,
        "limit": limit,
    }
    if alias is not None:
        channel = await get_channel(alias)
        if channel is None:
            return NotFoundResponse(f'alias "{alias}" does not exist')
        queries.append[ImageModel.channel == channel.id]
    if deleted is not None:
        queries.append(ImageModel.deleted == deleted)
    images = await Mongo.db.find(ImageModel, *queries, **options)
    if images:
        return images
    return NotFoundResponse("No items found")


@router.get(
    "/image/{attachment_id}",
    response_model=ImageModel,
    responses={404: {"model": NotFoundError}},
)
async def get_image_by_id(attachment_id: str):
    """Retrieves image document by attachment_id"""
    image = await get_image(attachment_id)
    if image is not None:
        return image
    return NotFoundResponse(f"attachment id {attachment_id} does not exist")


@router.get(
    "/channel",
    response_model=List[ChannelModel],
    responses={404: {"model": NotFoundError}},
)
async def get_channels():
    """Retrieves channel documents.
    Might add guild related filters in future
    """
    channels = await Mongo.db.find(ChannelModel)
    if channels:
        return channels
    return NotFoundResponse("No channels found")


@router.get(
    "/channel/{alias}",
    response_model=ChannelModel,
    responses={404: {"model": NotFoundError}},
)
async def get_channel_by_alias(alias: str):
    """retrives channel documents based on alias"""
    channel = await get_channel(alias)
    if channel is not None:
        return channel
    return NotFoundResponse(f'alias "{alias}" does not exist')


@router.get(
    "/count/image",
    response_model=int,
    responses={404: {"model": NotFoundError}},
)
async def get_image_count(
    alias: Optional[str] = None,
    deleted: Optional[bool] = None,
):
    """Counts number of images, if alias is not provided
    will count all images
    """
    queries: List[QueryExpression] = []
    if alias is not None:
        channel = await get_channel(alias)
        if channel is None:
            return NotFoundResponse(f'alias "{alias}" does not exist')
        queries.append(ImageModel.channel == channel.id)
    if deleted is not None:
        queries.append(ImageModel.deleted == deleted)
    return await Mongo.db.count(ImageModel, *queries)
