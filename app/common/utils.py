from enum import Enum
from datetime import datetime

from common.database import Mongo
from common.models import ChannelModel


class Order(str, Enum):
    asc = "asc"
    desc = "desc"


def get_seed(interval: int, offset: int) -> int:
    return int(datetime.now().timestamp() / interval) - (offset * 1000)


async def get_channel(alias: str) -> ChannelModel:
    channel = await Mongo.db.find_one(
        ChannelModel, ChannelModel.alias == alias
    )
    return channel
