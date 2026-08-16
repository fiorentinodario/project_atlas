from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.ai_assistant.providers import LLMProviderError
from project_atlas.decisions.schemas import parse_decision
from project_atlas.decisions.service import (
    accessible_decision,
    create_manual_decision,
    delete_decision,
    detect_decisions,
    list_decisions,
    review_decision,
    serialize_decision,
    update_decision,
)
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import User
from project_atlas.models.enums import DecisionStatus
from project_atlas.projects.service import accessible_project
from project_atlas.rag.providers import EmbeddingProviderError
from project_atlas.tasks.service import WRITE_ROLES

decisions_blueprint = Blueprint("decisions", __name__)


def _user() -> User:
    user = db.session.get(User, UUID(get_jwt_identity()))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)
    return user


def _status_filter() -> DecisionStatus | None:
    value = request.args.get("status")
    if not value:
        return None
    try:
        return DecisionStatus(value)
    except ValueError as error:
        raise ApiError("VALIDATION_ERROR", "Decision status filter is invalid.", 422) from error


@decisions_blueprint.get("/projects/<uuid:project_id>/decisions")
@jwt_required(locations=["headers"])
def index(project_id: UUID):
    decisions = list_decisions(project_id, _user().id, _status_filter())
    return jsonify({"data": {"items": [serialize_decision(item) for item in decisions]}})


@decisions_blueprint.post("/projects/<uuid:project_id>/decisions")
@jwt_required(locations=["headers"])
def create(project_id: UUID):
    user = _user()
    project, _role = accessible_project(project_id, user.id, WRITE_ROLES)
    decision = create_manual_decision(
        project, parse_decision(request.get_json(silent=True), partial=False), user
    )
    return jsonify({"data": {"decision": serialize_decision(decision)}}), 201


@decisions_blueprint.patch("/decisions/<uuid:decision_id>")
@jwt_required(locations=["headers"])
def update(decision_id: UUID):
    user = _user()
    decision, _role = accessible_decision(decision_id, user.id, write=True)
    decision = update_decision(
        decision, parse_decision(request.get_json(silent=True), partial=True), user
    )
    return jsonify({"data": {"decision": serialize_decision(decision)}})


@decisions_blueprint.delete("/decisions/<uuid:decision_id>")
@jwt_required(locations=["headers"])
def destroy(decision_id: UUID):
    user = _user()
    decision, _role = accessible_decision(decision_id, user.id, write=True)
    delete_decision(decision, user)
    return "", 204


@decisions_blueprint.post("/decisions/<uuid:decision_id>/<action>")
@jwt_required(locations=["headers"])
def review(decision_id: UUID, action: str):
    if action not in {"confirm", "reject"}:
        raise ApiError("NOT_FOUND", "The requested endpoint does not exist.", 404)
    user = _user()
    decision, _role = accessible_decision(decision_id, user.id, write=True)
    status = DecisionStatus.CONFIRMED if action == "confirm" else DecisionStatus.REJECTED
    decision = review_decision(decision, status, user)
    return jsonify({"data": {"decision": serialize_decision(decision)}})


@decisions_blueprint.post("/projects/<uuid:project_id>/decisions/detect")
@jwt_required(locations=["headers"])
def detect(project_id: UUID):
    user = _user()
    project, _role = accessible_project(project_id, user.id, WRITE_ROLES)
    try:
        decisions = detect_decisions(
            project,
            user,
            current_app.extensions["embedding_provider"],
            current_app.extensions["llm_provider"],
        )
    except EmbeddingProviderError as error:
        raise ApiError("EMBEDDING_UNAVAILABLE", str(error), 503) from error
    except LLMProviderError as error:
        raise ApiError("AI_DECISION_DETECTION_FAILED", str(error), 503) from error
    return jsonify({"data": {"items": [serialize_decision(item) for item in decisions]}}), 201
