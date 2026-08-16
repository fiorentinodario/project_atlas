from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from project_atlas.auth.schemas import parse_login, parse_registration
from project_atlas.auth.service import (
    authenticate_user,
    issue_token_pair,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
    serialize_user,
)
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import User

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


def _authentication_response(user: User, status_code: int = 200):
    access_token, refresh_token = issue_token_pair(user)
    response = jsonify({"data": {"access_token": access_token, "user": serialize_user(user)}})
    set_refresh_cookies(response, refresh_token)
    return response, status_code


@auth_blueprint.post("/register")
def register():
    user = register_user(parse_registration(request.get_json(silent=True)))
    return _authentication_response(user, 201)


@auth_blueprint.post("/login")
def login():
    user = authenticate_user(parse_login(request.get_json(silent=True)))
    return _authentication_response(user)


@auth_blueprint.post("/refresh")
@jwt_required(refresh=True, locations=["cookies"])
def refresh():
    access_token, refresh_token = rotate_refresh_token(get_jwt_identity(), get_jwt()["jti"])
    response = jsonify({"data": {"access_token": access_token}})
    set_refresh_cookies(response, refresh_token)
    return response


@auth_blueprint.post("/logout")
@jwt_required(refresh=True, locations=["cookies"])
def logout():
    revoke_refresh_token(get_jwt()["jti"])
    response = jsonify({"data": {"message": "Logged out successfully."}})
    unset_jwt_cookies(response)
    return response


@auth_blueprint.get("/me")
@jwt_required(locations=["headers"])
def current_user():
    user = db.session.get(User, UUID(get_jwt_identity()))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)
    return jsonify({"data": {"user": serialize_user(user)}})
