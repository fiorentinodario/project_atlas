from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import User
from project_atlas.models.enums import ProjectRole
from project_atlas.projects.schemas import parse_project_create, parse_project_update
from project_atlas.projects.service import (
    accessible_project,
    create_project,
    delete_project,
    list_projects,
    serialize_project,
    update_project,
)

projects_blueprint = Blueprint("projects", __name__, url_prefix="/projects")


def _current_user() -> User:
    user = db.session.get(User, UUID(get_jwt_identity()))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)
    return user


def _pagination() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR", "Pagination parameters must be integers.", 422
        ) from error
    if page < 1 or per_page < 1 or per_page > 100:
        raise ApiError("VALIDATION_ERROR", "Pagination parameters are outside allowed limits.", 422)
    return page, per_page


@projects_blueprint.get("")
@jwt_required(locations=["headers"])
def index():
    user = _current_user()
    page, per_page = _pagination()
    result = list_projects(user.id, page, per_page)
    return jsonify(
        {
            "data": {
                "items": [serialize_project(project, role) for project, role in result.items],
                "pagination": {
                    "page": result.page,
                    "per_page": result.per_page,
                    "total": result.total,
                    "pages": result.pages,
                },
            }
        }
    )


@projects_blueprint.post("")
@jwt_required(locations=["headers"])
def create():
    user = _current_user()
    project = create_project(parse_project_create(request.get_json(silent=True)), user)
    return jsonify({"data": {"project": serialize_project(project, ProjectRole.OWNER)}}), 201


@projects_blueprint.get("/<uuid:project_id>")
@jwt_required(locations=["headers"])
def show(project_id: UUID):
    project, role = accessible_project(project_id, _current_user().id)
    return jsonify({"data": {"project": serialize_project(project, role)}})


@projects_blueprint.patch("/<uuid:project_id>")
@jwt_required(locations=["headers"])
def update(project_id: UUID):
    user = _current_user()
    project, role = accessible_project(
        project_id,
        user.id,
        {ProjectRole.OWNER, ProjectRole.ADMIN},
    )
    project = update_project(project, parse_project_update(request.get_json(silent=True)), user)
    return jsonify({"data": {"project": serialize_project(project, role)}})


@projects_blueprint.delete("/<uuid:project_id>")
@jwt_required(locations=["headers"])
def destroy(project_id: UUID):
    project, _role = accessible_project(
        project_id,
        _current_user().id,
        {ProjectRole.OWNER},
    )
    delete_project(project)
    return "", 204
