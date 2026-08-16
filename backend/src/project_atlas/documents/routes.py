from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.documents.service import (
    DOCUMENT_WRITE_ROLES,
    accessible_document,
    create_document,
    delete_document,
    list_documents,
    serialize_document,
)
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import User
from project_atlas.projects.service import accessible_project

documents_blueprint = Blueprint("documents", __name__)


def _current_user() -> User:
    user = db.session.get(User, UUID(get_jwt_identity()))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)
    return user


@documents_blueprint.get("/projects/<uuid:project_id>/documents")
@jwt_required(locations=["headers"])
def index(project_id: UUID):
    documents = list_documents(project_id, _current_user().id)
    return jsonify({"data": {"items": [serialize_document(item) for item in documents]}})


@documents_blueprint.post("/projects/<uuid:project_id>/documents")
@jwt_required(locations=["headers"])
def create(project_id: UUID):
    user = _current_user()
    project, _role = accessible_project(project_id, user.id, DOCUMENT_WRITE_ROLES)
    document = create_document(project, user, request.files.get("file"))
    return jsonify({"data": {"document": serialize_document(document)}}), 201


@documents_blueprint.delete("/documents/<uuid:document_id>")
@jwt_required(locations=["headers"])
def destroy(document_id: UUID):
    user = _current_user()
    document = accessible_document(document_id, user.id, DOCUMENT_WRITE_ROLES)
    delete_document(document, user)
    return "", 204
