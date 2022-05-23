from flask import request
from flask_restful import Resource, abort, current_app
from flask_jwt_extended import jwt_required
from api.api.schemas import UserSchema
from api.models import User, Media
from api.auth.helpers import admin_only
from api.extensions import db
from api.commons import storage
from api.commons.pagination import paginate


class UserResource(Resource):
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

    method_decorators = [jwt_required()]

    def get(self, user_id):
        schema = UserSchema()
        user = User.query.get_or_404(user_id)
        return {"user": schema.dump(user)}

    def put(self, user_id):
        schema = UserSchema(partial=True)
        user = User.query.get(user_id)
        if user:
            user = schema.load(request.json, instance=user)

        db.session.commit()

        return {"msg": "user updated", "user": schema.dump(user)}

    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"msg": "user deleted"}


class UserList(Resource):
    """Creation and get_all

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

    method_decorators = [jwt_required()]

    def get(self):
        schema = UserSchema(many=True)
        query = User.query
        return paginate(query, schema)

    def post(self):
        schema = UserSchema()
        user = schema.load(request.json)

        db.session.add(user)
        db.session.commit()

        return {"msg": "user created", "user": schema.dump(user)}, 201

class MediaResource(Resource):
    """
        Resource for uploading, retrieving and removing
        files.
    """
    method_decorators = [jwt_required(optional=True)]

    def post(self, title: str, playlist: str = ''):
        """
            Put resource represented by title into database and
            cloud storage.
        """
        admin_only()
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
        admin_only()
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
        admin_only()
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

