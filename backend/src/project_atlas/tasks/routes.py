from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import User
from project_atlas.models.enums import TaskPriority, TaskStatus
from project_atlas.projects.service import accessible_project
from project_atlas.tasks.schemas import parse_task
from project_atlas.tasks.service import (
    WRITE_ROLES,
    accessible_task,
    create_task,
    delete_task,
    list_tasks,
    serialize_task,
    update_task,
)

tasks_blueprint = Blueprint("tasks", __name__)


def _current_user() -> User:
    user = db.session.get(User, UUID(get_jwt_identity()))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)
    return user


def _enum_query(name: str, enum_type):
    value = request.args.get(name)
    if not value:
        return None
    try:
        return enum_type(value)
    except ValueError as error:
        raise ApiError("VALIDATION_ERROR", f"Task {name} filter is invalid.", 422) from error


def _pagination() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR", "Pagination parameters must be integers.", 422
        ) from error
    if page < 1 or per_page < 1 or per_page > 100:
        raise ApiError("VALIDATION_ERROR", "Pagination parameters are outside allowed limits.", 422)
    return page, per_page


@tasks_blueprint.get("/projects/<uuid:project_id>/tasks")
@jwt_required(locations=["headers"])
def index(project_id: UUID):
    page, per_page = _pagination()
    search = request.args.get("search", "").strip() or None
    if search and len(search) > 100:
        raise ApiError("VALIDATION_ERROR", "Task search must not exceed 100 characters.", 422)
    result = list_tasks(
        project_id,
        _current_user().id,
        page,
        per_page,
        _enum_query("status", TaskStatus),
        _enum_query("priority", TaskPriority),
        search,
    )
    return jsonify(
        {
            "data": {
                "items": [serialize_task(task) for task in result.items],
                "pagination": {
                    "page": result.page,
                    "per_page": result.per_page,
                    "total": result.total,
                    "pages": result.pages,
                },
            }
        }
    )


@tasks_blueprint.post("/projects/<uuid:project_id>/tasks")
@jwt_required(locations=["headers"])
def create(project_id: UUID):
    user = _current_user()
    project, _role = accessible_project(project_id, user.id, WRITE_ROLES)
    task = create_task(project, parse_task(request.get_json(silent=True), partial=False), user)
    return jsonify({"data": {"task": serialize_task(task)}}), 201


@tasks_blueprint.patch("/tasks/<uuid:task_id>")
@jwt_required(locations=["headers"])
def update(task_id: UUID):
    user = _current_user()
    task, _role = accessible_task(task_id, user.id, write=True)
    task = update_task(task, parse_task(request.get_json(silent=True), partial=True), user)
    return jsonify({"data": {"task": serialize_task(task)}})


@tasks_blueprint.delete("/tasks/<uuid:task_id>")
@jwt_required(locations=["headers"])
def destroy(task_id: UUID):
    user = _current_user()
    task, _role = accessible_task(task_id, user.id, write=True)
    delete_task(task, user)
    return "", 204
