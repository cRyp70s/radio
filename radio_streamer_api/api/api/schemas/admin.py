from api.models import Media
from api.extensions import ma, db


class AddPlaylistSchema(ma.SQLAlchemyAutoSchema):
    id = ma.Int(dump_only=True)
    playlist = ma.String(required=True)
    title = ma.String(required=True)
    audio_url = ma.String(required=True)
    thumbnail_image_url = ma.String(required=True)

class PlayFromPlaylistSchema(ma.Schema):
    playlist = ma.String(required=True)
    name = ma.String(required=True)
    audio_url = ma.String(required=True)
    thumbnail_image_url = ma.String(required=True)

class DeletePlaylistSchema(ma.Schema):
    playlist = ma.String(required=True)
    name = ma.String()