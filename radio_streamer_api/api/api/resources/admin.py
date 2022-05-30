from email import message
import requests
from sqlalchemy import and_
from flask import request, jsonify
from flask_restful import Resource, abort, current_app
from flask_jwt_extended import jwt_required, current_user

from api.commons.redis import redis_backend

from api.api.schemas.admin import (
  AddPlaylistSchema,
  PlayFromPlaylistSchema,
  DeletePlaylistSchema)
from api.models import User, Media
from api.extensions import db
from api.config import STORAGE_URL
from api.commons.pagination import paginate
from api.auth.helpers import admin_required

from api.commons import storage


class Play(Resource):
    """Play songs from a playlist

    ---
    post:
      tags:
        - play
      summary: Play songs
      description: play songs
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                playlist:
                  type: string

      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  playlist:
                    type: string
                  songs:
                    type: array
                    items:
                      type: string
        404:
          description: playlist does not exist
    """

    method_decorators = [admin_required, jwt_required()]

    def post(self):
        # user_id = get_jwt_identity()
        # in_schema = PlayFromPlaylistRequestSchema()
        media = request.json
        playlist = media["playlist"]
        out = {"playlist": playlist}
        out_songs = []
        medias = Media.query.filter(Media.playlist==playlist).all()
        promos = []
        promotions = Media.query.filter(Media.playlist=='promotion').all()
        
        # set promotions to be played
        for p in promotions:
            promos.append((p.audio_name, p.audio_url, p.thumbnail_image_url))
        redis_backend.set("CURRENT_PROMOTIONS", promos)
        if not medias:
              abort(404, message="playlist not found")
        for m in medias:
            out_songs.append((m.title, m.audio_url, m.thumbnail_image_url))
        out["songs"] = out_songs
        redis_backend.set("CURRENT_PLAY", out)
        redis_backend.set("CURRENT_THUMB", out[1][0][-1])
        return jsonify(out)


class PlayList(Resource):
    """
        Creating playlists and 

    ---
    get:
      tags:
        - playlist
      summary: Get playlist and content
      description: Get playlist content
      parameters:
        - in: query
          name: page
          schema:
            type: integer
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
                          schema: AddPlaylistSchema
    post:
      tags:
        - playlist
      summary: Add song to playlist
      description: Add to playlist
      requestBody:
        content:
          application/json:
            schema:
              AddPlaylistSchema
      responses:
        201:
          content:
            application/json:
              schema:
                type: null
    delete:
      tags:
        - playlist
      summary: Delete song from playlist
      description: Delete to playlist
      responses:
        201:
          content:
            application/json:
              schema:
                type: null
    """

    method_decorators = [admin_required, jwt_required()]

    def get(self, playlist, title=''):
        """
        """
        schema = AddPlaylistSchema(many=True)
        query = Media.query
        query = query.filter_by(playlist=playlist)
        if title and title != '*':
              query = query.filter_by(title=title)
        return paginate(query, schema)

    def post(self):
        """
            
        """
        schema = AddPlaylistSchema()
        media_load = schema.load(request.json)
        media = Media(playlist = media_load["playlist"],
                      title=media_load["title"],
                      audio_url=media_load["audio_url"],
                      thumbnail_image_url=media_load["thumbnail_image_url"],
                      setter_id = current_user.id)
        db.session.add(media)
        db.session.commit()
        return "", 201
    
    def delete(self, playlist, title):
        """
            
        """
        schema = DeletePlaylistSchema()
        if title == "*":
              query = Media.query.filter(Media.playlist==playlist)
        else:
          query = Media.query.filter(and_(Media.title==title, Media.playlist==playlist))
        query.first_or_404()
        query.delete()
        db.session.commit()

        return

class PlayListAll(Resource):
    """
        Get available playlists

    ---
    get:
      tags:
        - playlist
      summary: Get playlists
      description: Get playlists
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  playlists:
                    type: array
                    items:
                      type: string
    """

    method_decorators = [admin_required, jwt_required()]

    def get(self, playlist, title=''):
        """
        """
        query = Media.query
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
        
        # Update or Create
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
        
        misc = {"aud_id": aud_upload["id"], "thumb_id": thumb_upload["id"]}
        media.misc = misc
        media.audio_url = aud_upload["url"]
        media.thumbnail_image_url = thumb_upload["url"]
        db.session.add(media)
        db.session.commit()
        return {"thumb_url": media.thumbnail_image_url,
                "media_url": media.audio_url}, 201
    
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
            media = query.all()
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
            abort(404, message="resource not found")
        try:
            query.delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(e)
            abort(500)
        return ""
    
    def get(self, title: str = '', playlist: str = ''):
        """
            Return the data for title and playlist or get all
            data for a playlist.
        """
        if not any([playlist, title]):
            abort(400)
        
        if title and title != '*':
            # request single song
            items = Media.query.filter_by(title=title, playlist=playlist).all()
        else:
            # request playlist
            items = Media.query.filter_by(playlist=playlist).all()
        if not items:
            abort(404, message="resource not found")
        return [{
                "title": media.title, 
                "thumbnail": media.thumbnail_image_url,
                "media": media.audio_url,
                "playlist": media.playlist
                } for media in items]