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
    """
        Creation and get_all
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
      Creation and get_all
    """

    def get(self):
        curr_song = redis_backend.get("CURRENT_SONG")
        curr_thumb = redis_backend.get("CURRENT_THUMB")
        return {"song_name": curr_song, "thumbnail": curr_thumb}
        