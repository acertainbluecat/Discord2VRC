from typing import List, Optional

from pydantic import BaseModel
from bson.objectid import ObjectId
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=0),
    order: Order = Order.desc,
    deleted: Optional[bool] = None,
):
    """Retrieves image documents, if alias is not provided
    will retrieve all images.
    """
    queries: List = []
    options = {
        "sort": getattr(ImageModel.attachment_id, order.value)(),
        "skip": skip,
        "limit": limit,
    }
    if alias is not None:
        channel = await get_channel(alias)
        if channel is None:
            return NotFoundResponse(f'alias "{alias}" does not exist')
        queries.append(ImageModel.channel == channel.id)
    if deleted is not None:
        queries.append(ImageModel.deleted == deleted)
    images = await Mongo.db.find(ImageModel, *queries, **options)
    if images:
        return images
    return NotFoundResponse("No items found")


@router.get(
    "/randomimage",
    response_model=List[ImageModel],
    responses={404: {"model": NotFoundError}},
)
async def get_random_images(
    alias: Optional[str] = None,
    limit: int = Query(100, ge=0),
    deleted: Optional[bool] = None,
):
    """Retrieves randomized list of image documents"""
    pipeline = [
        {
            "$lookup": {
                "from": "channel",
                "localField": "channel",
                "foreignField": "_id",
                "as": "channel",
            }
        },
        {"$unwind": {"path": "$channel"}},
        {"$sample": {"size": limit}},
    ]
    match = []
    if alias is not None:
        channel = await get_channel(alias)
        if channel is None:
            return NotFoundResponse(f'alias "{alias}" does not exist')
        match.append(("channel", ObjectId(channel.id)))
    if deleted is not None:
        match.append(("deleted", deleted))

    images = Mongo.db.get_collection(ImageModel)
    if match:
        pipeline.insert(0, {"$match": {k: v for k, v in match}})
    result = await images.aggregate(pipeline).to_list(length=limit)
    if result:
        return [ImageModel.parse_doc(doc) for doc in result]
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
    queries: List = []
    if alias is not None:
        channel = await get_channel(alias)
        if channel is None:
            return NotFoundResponse(f'alias "{alias}" does not exist')
        queries.append(ImageModel.channel == channel.id)
    if deleted is not None:
        queries.append(ImageModel.deleted == deleted)
    return await Mongo.db.count(ImageModel, *queries)
