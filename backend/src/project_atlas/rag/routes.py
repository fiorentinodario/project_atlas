from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.documents.service import DOCUMENT_WRITE_ROLES, accessible_document
from project_atlas.errors import ApiError
from project_atlas.projects.service import accessible_project
from project_atlas.rag.indexing import index_document
from project_atlas.rag.providers import EmbeddingProviderError
from project_atlas.rag.retrieval import retrieve_chunks

rag_blueprint = Blueprint("rag", __name__)


def _user_id() -> UUID:
    return UUID(get_jwt_identity())


@rag_blueprint.post("/documents/<uuid:document_id>/index")
@jwt_required(locations=["headers"])
def reindex(document_id: UUID):
    document = accessible_document(document_id, _user_id(), DOCUMENT_WRITE_ROLES)
    provider = current_app.extensions["embedding_provider"]
    index_document(document, provider, force=True)
    if document.indexing_error:
        raise ApiError("EMBEDDING_UNAVAILABLE", document.indexing_error, 503)
    return jsonify(
        {
            "data": {
                "document_id": str(document.id),
                "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None,
            }
        }
    )


@rag_blueprint.post("/projects/<uuid:project_id>/search")
@jwt_required(locations=["headers"])
def search(project_id: UUID):
    accessible_project(project_id, _user_id())
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("INVALID_REQUEST", "A JSON object is required.", 400)
    query = payload.get("query")
    limit = payload.get("limit", 5)
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 500:
        raise ApiError("VALIDATION_ERROR", "Search query must contain 2 to 500 characters.", 422)
    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ApiError("VALIDATION_ERROR", "Search limit must be between 1 and 10.", 422)
    try:
        results = retrieve_chunks(
            project_id,
            query.strip(),
            current_app.extensions["embedding_provider"],
            limit,
        )
    except EmbeddingProviderError as error:
        raise ApiError("EMBEDDING_UNAVAILABLE", str(error), 503) from error
    return jsonify(
        {
            "data": {
                "items": [
                    {
                        "chunk_id": str(item.chunk.id),
                        "content": item.chunk.content,
                        "page_number": item.chunk.page_number,
                        "score": round(item.score, 6),
                        "document": {
                            "id": str(item.document.id),
                            "filename": item.document.filename,
                        },
                    }
                    for item in results
                ]
            }
        }
    )
