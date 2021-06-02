from datetime import datetime
from odmantic import Model, Field, Reference

class Channel(Model):
    channel_id:     int
    channel_name:   str
    alias:          str
    guild:          str
    guild_id:       int
    subscribed:     bool = True

class Image(Model):
    filename:       str
    filepath:       str
    attachment_id:  int
    channel:        Channel = Reference()
    username:       str
    user_num:       str
    user_id:        int
    message_id:     int
    created_at:     datetime
    retrieved_at:   datetime = Field(default_factory = datetime.utcnow)
    deleted:        bool = False
    