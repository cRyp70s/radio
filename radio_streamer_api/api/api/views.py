from flask import Blueprint, current_app, jsonify
from flask_restful import Api
from marshmallow import ValidationError
from api.extensions import apispec
from api.api.resources.resources import UserList, CurrentPlay
from api.api.resources.admin import MediaResource, PlayList, Play
from api.api.schemas import UserSchema


blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(blueprint)


# Resource
api.add_resource(UserList, "/users", "/users/<int:user_id>", endpoint="users")
api.add_resource(CurrentPlay, "/current-play", endpoint="current_play")

# Admin resources
api.add_resource(MediaResource, "/media", "/media/<title>", 
                 "/media/<title>/<playlist>", endpoint="media")
api.add_resource(PlayList, "/playlist/<playlist>", "/playlist/<playlist>/<title>",
                 "/playlist", endpoint="playlist")
api.add_resource(Play, "/play", endpoint="play")


@blueprint.errorhandler(ValidationError)
def handle_marshmallow_error(e):
    """Return json error for marshmallow validation errors.

    This will avoid having to try/catch ValidationErrors in all endpoints, returning
    correct JSON response with associated HTTP 400 Status (https://tools.ietf.org/html/rfc7231#section-6.5.1)
    """
    return jsonify(e.messages), 400
