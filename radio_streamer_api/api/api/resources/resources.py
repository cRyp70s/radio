from flask import request
from flask_restful import Resource, abort, current_app
from flask_jwt_extended import jwt_required, get_current_user
from api.api.schemas import UserSchema
from api.models import User
from api.auth.helpers import admin_only, admin_required
from api.extensions import db
from api.commons.pagination import paginate
from api.commons.redis import redis_backend


class UserList(Resource):
    """User creation, view and delete resource
    ---
    get:
      tags:
        - users
      summary: Get a user
      description: Get a single user by id
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
    post:
      tags:
        - users
      summary: Create a user
      description: Create a single user
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
        404:
          description: user does not exists
    delete:
      tags:
        - users
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

    method_decorators = [jwt_required(optional=True)]

    def get(self, user_id):
        user = get_current_user()
        if user.id != user_id and not user.is_admin:
            abort(401)
        user = User.query.get_or_404(user_id)
        schema = UserSchema()
        return {"user": schema.dump(user)}

    def post(self):
        schema = UserSchema()
        user = schema.load(request.json)

        db.session.add(user)
        db.session.commit()

        return {"msg": "user created", "user": schema.dump(user)}, 201
    
    def delete(self, user_id):
        user = get_current_user()
        if user.id != user_id and not user.is_admin:
            abort(401)
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"msg": "user deleted"}

class CurrentPlay(Resource):
    """
      Get currently playing song data
      ---
      get:
        summary: Get currently playing song.
        tags:
          - current_play
        responses:
          200:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    song_name: 
                      type: string
                    thumbnail: 
                      type: string
    """

    def get(self):
        curr_song = redis_backend.get("CURRENT_SONG")
        curr_thumb = redis_backend.get("CURRENT_THUMB")
        return {"song_name": curr_song, "thumbnail": curr_thumb}
        