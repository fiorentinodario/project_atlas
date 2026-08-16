from uuid import UUID

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.ai_assistant.providers import LLMProviderError
from project_atlas.analyses.service import analyze_project, latest_analysis, serialize_analysis
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import User
from project_atlas.projects.service import accessible_project
from project_atlas.tasks.service import WRITE_ROLES

analyses_blueprint = Blueprint("analyses", __name__)


def _user() -> User:
    user = db.session.get(User, UUID(get_jwt_identity()))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)
    return user


@analyses_blueprint.get("/projects/<uuid:project_id>/analyses/latest")
@jwt_required(locations=["headers"])
def latest(project_id: UUID):
    analysis = latest_analysis(project_id, _user().id)
    return jsonify({"data": {"analysis": serialize_analysis(analysis) if analysis else None}})


@analyses_blueprint.post("/projects/<uuid:project_id>/analyses")
@jwt_required(locations=["headers"])
def create(project_id: UUID):
    user = _user()
    project, _role = accessible_project(project_id, user.id, WRITE_ROLES)
    try:
        analysis = analyze_project(
            project,
            user,
            current_app.extensions["embedding_provider"],
            current_app.extensions["llm_provider"],
        )
    except LLMProviderError as error:
        raise ApiError("AI_ANALYSIS_FAILED", str(error), 503) from error
    return jsonify({"data": {"analysis": serialize_analysis(analysis)}}), 201
