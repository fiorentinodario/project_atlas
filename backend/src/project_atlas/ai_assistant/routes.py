from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.ai_assistant.providers import LLMProviderError
from project_atlas.ai_assistant.service import answer_project_question
from project_atlas.errors import ApiError
from project_atlas.projects.service import accessible_project

assistant_blueprint = Blueprint("assistant", __name__)


def _validated_history(payload: dict) -> list[dict[str, str]]:
    history = payload.get("history", [])
    if not isinstance(history, list) or len(history) > 10:
        raise ApiError("VALIDATION_ERROR", "History must contain at most 10 messages.", 422)
    validated = []
    for message in history:
        if not isinstance(message, dict):
            raise ApiError("VALIDATION_ERROR", "History contains an invalid message.", 422)
        role = message.get("role")
        content = message.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            raise ApiError("VALIDATION_ERROR", "History contains an invalid message.", 422)
        if not 1 <= len(content.strip()) <= 2000:
            raise ApiError("VALIDATION_ERROR", "History contains an invalid message.", 422)
        validated.append({"role": role, "content": content.strip()})
    return validated


@assistant_blueprint.post("/projects/<uuid:project_id>/assistant/messages")
@jwt_required(locations=["headers"])
def create_message(project_id: UUID):
    project, _role = accessible_project(project_id, UUID(get_jwt_identity()))
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("INVALID_REQUEST", "A JSON object is required.", 400)
    question = payload.get("question")
    if not isinstance(question, str) or not 2 <= len(question.strip()) <= 1000:
        raise ApiError("VALIDATION_ERROR", "Question must contain 2 to 1000 characters.", 422)
    try:
        answer = answer_project_question(
            project,
            question.strip(),
            current_app.extensions["embedding_provider"],
            current_app.extensions["llm_provider"],
            _validated_history(payload),
        )
    except LLMProviderError as error:
        raise ApiError("AI_ASSISTANT_UNAVAILABLE", str(error), 503) from error
    return jsonify(
        {
            "data": {
                "message": {
                    "role": "assistant",
                    "content": answer.content,
                    "sources": [
                        {
                            "number": source.number,
                            "chunk_id": source.chunk_id,
                            "document_id": source.document_id,
                            "filename": source.filename,
                            "page_number": source.page_number,
                            "excerpt": source.excerpt,
                            "score": source.score,
                        }
                        for source in answer.sources
                    ],
                }
            }
        }
    )
