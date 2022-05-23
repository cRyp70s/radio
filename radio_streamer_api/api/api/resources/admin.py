import requests
from sqlalchemy import and_
from flask import request, jsonify
from flask_restful import Resource, abort, current_app
from flask_jwt_extended import jwt_required, current_user

from common.redis import redis_backend

from api.api.schemas.admin import (
  AddPlaylistSchema,
  PlayFromPlaylistSchema,
  DeletePlaylistSchema,
  PlayFromPlaylistRequestSchema)
from api.models import User, Media
from api.extensions import db
from api.config import STORAGE_URL
from api.commons.pagination import paginate
from api.auth.helpers import admin_required

from api.commons import storage


class Play(Resource):
    """Single object resource

    ---
    get:
      tags:
        - api
      summary: Get a user
      description: Get a single user by ID
      parameters:
        - in: path
          name: user_id
          schema:
            type: integer
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  user: UserSchema
        404:
          description: user does not exists
    put:
      tags:
        - api
      summary: Update a user
      description: Update a single user by ID
      parameters:
        - in: path
          name: user_id
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              UserSchema
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: user updated
                  user: UserSchema
        404:
          description: user does not exists
    delete:
      tags:
        - api
      summary: Delete a user
      description: Delete a single user by ID
      parameters:
        - in: path
          name: user_id
          schema:
            type: integer
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: user deleted
        404:
          description: user does not exists
    """

    method_decorators = [admin_required, jwt_required()]

    def post(self):
        # user_id = get_jwt_identity()
        in_schema = PlayFromPlaylistRequestSchema()
        media = in_schema.load(request.json)
        playlist = media["playlist"]
        songs = media.get("songs")
        out = [playlist]
        out_songs = []
        # for song in songs:
            # resp = requests.get(f"{STORAGE_URL}/media/{song}/{playlist}")
            # if not resp.ok:
            #     abort(resp.status_code, message=str(resp.content))
            # resp = resp.json()[0]
            # print(resp)
            # out_songs.append((resp["title"], resp["media"], resp["thumbnail"]))
        medias = Media.query.filter(Media.playlist==playlist).all()
        promos = []
        promotions = Media.query.filter(Media.playlist=='promotion').all()
        for p in promotions:
            promos.append((p.audio_name, p.audio_url, p.thumbnail_url))
        redis_backend.set("CURRENT_PROMOTIONS", promos)
        for m in medias:
            out_songs.append((m.audio_name, m.audio_url, m.thumbnail_url))
        out.append(out_songs)
        redis_backend.set("CURRENT_PLAY", out)
        redis_backend.set("CURRENT_THUMB", out[1][0][-1])
        return jsonify(out)


class PlayList(Resource):
    """
        Creating playlists and 

    ---
    get:
      tags:
        - api
      summary: Get a list of users
      description: Get a list of paginated users
      responses:
        200:
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResult'
                  - type: object
                    properties:
                      results:
                        type: array
                        items:
                          $ref: '#/components/schemas/UserSchema'
    post:
      tags:
        - api
      summary: Create a user
      description: Create a new user
      requestBody:
        content:
          application/json:
            schema:
              UserSchema
      responses:
        201:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: user created
                  user: UserSchema
    """

    method_decorators = [admin_required, jwt_required()]

    def get(self, playlist, song=''):
        """
        """
        schema = AddPlaylistSchema(many=True)
        query = Media.query
        if request.args.get("playlists_only") == "true":
              all = query.all()
              playlists = []
              already = []
              i = 0
              for pl in all:
                    plist = pl.playlist
                    if plist not in already:  
                      already.append(plist)
                      playlists.append([i, plist])
                      i += 1
              return {"playlists": list(playlists)}
        if playlist and playlist != '*':
              query = query.filter_by(playlist=playlist)
        if song and song != '*':
              query = query.filter_by(audio_name=song)
        return paginate(query, schema)

    def post(self):
        """
            
        """
        # promotions = redis_backend.get("CURRENT_PROMOTIONS")
        schema = AddPlaylistSchema()
        media_load = schema.load(request.json)
        media = Media(playlist = media_load["playlist"],
                      audio_name=media_load["audio_name"],
                      audio_url=media_load["audio_url"],
                      thumbnail_url=media_load["thumbnail_url"],
                      setter_id = current_user.id)
        # help(media)
        db.session.add(media)
        db.session.commit()
    
    def delete(self, playlist, song):
        """
            
        """
        schema = DeletePlaylistSchema()
        if song == "*":
              query = Media.query.filter(Media.playlist==playlist)
        else:
          query = Media.query.filter(and_(Media.audio_name==song, Media.playlist==playlist))
        query.delete()
        db.session.commit()

        return {"msg": "media deleted"}, 201


class MediaResource(Resource):
    """
        Resource for uploading, retrieving and removing
        files.
    """
    method_decorators = [admin_required, jwt_required(optional=True)]

    def post(self, title: str, playlist: str = ''):
        """
            Put resource represented by title into database and
            cloud storage.
        """
        media = Media.query.filter_by(title=title, playlist=playlist).first()
        if media:
            media.title = title
            media.playlist = playlist
        else:
            media = Media(title=title, playlist=playlist)
        files  = request.files
        thumbnail = files.get("thumbnail")
        try:
            audio = files["audio"]
        except KeyError:
            abort(400, message="audio file must be provided")
        aud_upload = storage.upload_media(audio, title, playlist=playlist)
        thumb_upload = storage.upload_media(thumbnail, title, "jpg", playlist=playlist)
        print(thumb_upload, aud_upload)
        misc = {"aud_id": aud_upload["id"], "thumb_id": thumb_upload["id"]}
        media.misc = misc
        media.media_url = aud_upload["url"]
        media.thumbnail_image_url = thumb_upload["url"]
        db.session.add(media)
        db.session.commit()
        return {"thumb_url": media.thumbnail_image_url,
                "media_url": media.media_url}
    
    def delete(self, title: str = '', playlist: str = ''):
        """
            Delete resource represented by title
            from database and cloud storage.
        """
        logger = current_app.logger
        if not any([title, playlist]):
            abort(400)

        if title:
            query = Media.query.filter_by(title=title, playlist=playlist)
            media = [query.first()]
        else:
            query = Media.query.filter_by(playlist=playlist)
            media = query.all()
        
        for item in media:
            misc = item.misc
            try:
                storage.delete_media(misc["aud_id"])
                storage.delete_media(misc["thumb_id"])
            except Exception as e:
                logger.error(e)

        if not media:
            abort(404)
        try:
            query.delete()
            db.session.commit()
        except Exception as e:
            logger.error(e)
            return {"status": "error"}
        return {"status": "success"}
    
    def get(self, title: str = '', playlist: str = ''):
        """
            Return the data for title and playlist or get all
            data for a playlist.
        """
        if not any([playlist, title]):
            abort(400)
        
        if title and title != '*':
            # request single song
            items = [Media.query.filter_by(title=title, playlist=playlist).first()]
        else:
            # request playlist
            items = Media.query.filter_by(playlist=playlist).all()
        if not any(items):
            abort(404)
        return [{
                "title": media.title, 
                "thumbnail": media.thumbnail_image_url,
                "media": media.media_url,
                "playlist": media.playlist
                } for media in items]