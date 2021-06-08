from datetime import datetime
from odmantic import Model, Field, Reference


class ChannelModel(Model):
    """Discord channels"""

    channel_id: str
    channel_name: str
    alias: str
    guild: str
    guild_id: str
    subscribed: bool = True


class ImageModel(Model):
    """Image attachments from discord"""

    filename: str
    filepath: str
    attachment_id: str
    channel: ChannelModel = Reference()
    username: str
    user_num: str
    user_id: str
    message_id: str
    created_at: datetime
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    deleted: bool = False
