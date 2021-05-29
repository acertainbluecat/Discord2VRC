from datetime import datetime
from odmantic import Model

class Image(Model):
    filename:       str
    filepath:       str
    attachment_id:  int
    guild:          str
    guild_id:       int
    channel:        str
    channel_id:     int
    username:       str
    user_num:       str
    user_id:        int
    created_at:     datetime = datetime.utcnow()
