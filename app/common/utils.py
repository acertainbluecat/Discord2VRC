from enum import Enum
from typing import Optional
from datetime import datetime

from common.database import Mongo
from common.models import ChannelModel, ImageModel


class Order(str, Enum):
    asc = "asc"
    desc = "desc"


def get_seed(interval: int, offset: int) -> int:
    """gets a seed based on unix timestamp.
    interval divides the timestamp, providing a time interval range
    where the seed would be the same.
    offset simply offsets the value of the seed by 1000
    """
    return int(datetime.now().timestamp() / interval) - (offset * 1000)


async def get_channel(alias: str) -> Optional[ChannelModel]:
    """Gets channel based on alias"""
    channel = await Mongo.db.find_one(
        ChannelModel, ChannelModel.alias == alias
    )
    return channel


async def get_image(attachment_id: str) -> Optional[ImageModel]:
    """Gets image based on attachment id"""
    image = await Mongo.db.find_one(
        ImageModel, ImageModel.attachment_id == attachment_id
    )
    return image
