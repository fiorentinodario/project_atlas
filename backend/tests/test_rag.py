from io import BytesIO

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import func, select

from project_atlas.extensions import db
from project_atlas.models import Document, DocumentChunk
from project_atlas.rag.chunking import TokenChunker


class FakeEmbeddingProvider:
    dimensions = 1536

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            vector = [0.0] * self.dimensions
            normalized = text.lower()
            if "authentication" in normalized or "login" in normalized:
                vector[0] = 1.0
            elif "budget" in normalized or "cost" in normalized:
                vector[1] = 1.0
            else:
                vector[2] = 1.0
            embeddings.append(vector)
        return embeddings


def register(client: FlaskClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"display_name": "Rag User", "email": email, "password": "securepass123"},
    )
    return response.get_json()["data"]["access_token"]


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_project(client: FlaskClient, token: str, name: str = "RAG project") -> str:
    response = client.post("/api/v1/projects", json={"name": name}, headers=authorization(token))
    return response.get_json()["data"]["project"]["id"]


def upload_text(client: FlaskClient, project_id: str, token: str, text: str, filename: str):
    return client.post(
        f"/api/v1/projects/{project_id}/documents",
        data={"file": (BytesIO(text.encode()), filename, "text/plain")},
        headers=authorization(token),
        content_type="multipart/form-data",
    )


def test_chunker_preserves_pages_and_overlap() -> None:
    chunker = TokenChunker(chunk_size=4, overlap=1)

    chunks = chunker.chunk("one two three four five six\fsecond page")

    assert [chunk.page_number for chunk in chunks] == [1, 1, 2]
    assert chunks[0].content == "one two three four"
    assert chunks[1].content.startswith("four ")
    assert chunks[0].token_count == 4


def test_upload_indexes_and_searches_with_citations(app: Flask, client: FlaskClient) -> None:
    app.extensions["embedding_provider"] = FakeEmbeddingProvider()
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)
    upload_text(
        client,
        project_id,
        token,
        "Authentication uses short-lived JWT access tokens.",
        "security.txt",
    )
    upload_text(client, project_id, token, "The approved budget is 5000 euros.", "budget.txt")

    response = client.post(
        f"/api/v1/projects/{project_id}/search",
        json={"query": "How does authentication work?", "limit": 2},
        headers=authorization(token),
    )

    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    assert items[0]["document"]["filename"] == "security.txt"
    assert items[0]["page_number"] == 1
    assert items[0]["score"] == 1.0
    with app.app_context():
        document = db.session.scalar(select(Document).where(Document.filename == "security.txt"))
        assert document.indexed_at is not None
        assert document.indexing_error is None
        assert db.session.scalar(select(func.count(DocumentChunk.id))) == 2


def test_search_is_scoped_to_authorized_project(app: Flask, client: FlaskClient) -> None:
    app.extensions["embedding_provider"] = FakeEmbeddingProvider()
    owner_token = register(client, "owner@example.com")
    outsider_token = register(client, "outsider@example.com")
    project_id = create_project(client, owner_token)
    upload_text(client, project_id, owner_token, "Authentication details", "private.txt")

    response = client.post(
        f"/api/v1/projects/{project_id}/search",
        json={"query": "authentication"},
        headers=authorization(outsider_token),
    )

    assert response.status_code == 404


def test_disabled_provider_keeps_chunks_and_returns_service_unavailable(
    app: Flask, client: FlaskClient
) -> None:
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)
    uploaded = upload_text(client, project_id, token, "Offline document", "offline.txt")

    response = client.post(
        f"/api/v1/projects/{project_id}/search",
        json={"query": "offline"},
        headers=authorization(token),
    )

    assert uploaded.status_code == 201
    assert uploaded.get_json()["data"]["document"]["status"] == "READY"
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "EMBEDDING_UNAVAILABLE"
    with app.app_context():
        assert db.session.scalar(select(func.count(DocumentChunk.id))) == 1
