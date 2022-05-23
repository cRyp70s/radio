from flask import request
from flask_restful import Resource, abort, current_app
from flask_jwt_extended import jwt_required
from api.api.schemas import UserSchema
from api.models import User
from api.auth.helpers import admin_only, admin_required
from api.extensions import db
from api.commons.pagination import paginate
from common.redis import redis_backend


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

    method_decorators = [jwt_required(optional=True)]

    def get(self, user_id):
        schema = UserSchema()
        user = User.query.get_or_404(user_id)
        return {"user": schema.dump(user)}

    def post(self):
        schema = UserSchema()
        user = schema.load(request.json)

        db.session.add(user)
        db.session.commit()

        return {"msg": "user created", "user": schema.dump(user)}, 201
    
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"msg": "user deleted"}

class CurrentPlay(Resource):
    """
      Creation and get_all
    """

    def get(self):
        curr_song = redis_backend.get("CURRENT_SONG")
        curr_thumb = redis_backend.get("CURRENT_THUMB")
        return {"song_name": curr_song, "thumbnail": curr_thumb}
        