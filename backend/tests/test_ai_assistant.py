from io import BytesIO

from flask import Flask
from flask.testing import FlaskClient


class FakeEmbeddingProvider:
    dimensions = 1536

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for _ in texts:
            vector = [0.0] * self.dimensions
            vector[0] = 1.0
            vectors.append(vector)
        return vectors


class FakeLLMProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self) -> None:
        self.system_prompt = ""
        self.user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return "The project requires JWT authentication [1]."


def register(client: FlaskClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"display_name": "Assistant User", "email": email, "password": "securepass123"},
    )
    return response.get_json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_project(client: FlaskClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Atlas", "description": "Internal project platform"},
        headers=auth(token),
    )
    return response.get_json()["data"]["project"]["id"]


def upload_context(client: FlaskClient, project_id: str, token: str) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents",
        data={
            "file": (
                BytesIO(b"Authentication uses short-lived JWT access tokens."),
                "requirements.txt",
                "text/plain",
            )
        },
        headers=auth(token),
        content_type="multipart/form-data",
    )
    assert response.status_code == 201


def test_assistant_answers_from_project_context(app: Flask, client: FlaskClient) -> None:
    embedding_provider = FakeEmbeddingProvider()
    llm_provider = FakeLLMProvider()
    app.extensions["embedding_provider"] = embedding_provider
    app.extensions["llm_provider"] = llm_provider
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)
    upload_context(client, project_id, token)

    response = client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={
            "question": "What authentication is required?",
            "history": [{"role": "user", "content": "Tell me about security."}],
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    message = response.get_json()["data"]["message"]
    assert message["role"] == "assistant"
    assert message["content"] == "The project requires JWT authentication [1]."
    assert message["sources"][0] == {
        "number": 1,
        "chunk_id": message["sources"][0]["chunk_id"],
        "document_id": message["sources"][0]["document_id"],
        "filename": "requirements.txt",
        "page_number": 1,
        "excerpt": "Authentication uses short-lived JWT access tokens.",
        "score": 1.0,
    }
    assert "Answer only from the supplied project context" in llm_provider.system_prompt
    assert "matching source marker" in llm_provider.system_prompt
    assert "Name: Atlas" in llm_provider.user_prompt
    assert "requirements.txt" in llm_provider.user_prompt
    assert "short-lived JWT access tokens" in llm_provider.user_prompt
    assert "Tell me about security" in llm_provider.user_prompt


def test_assistant_rejects_invalid_question(client: FlaskClient) -> None:
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)

    response = client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"question": " "},
        headers=auth(token),
    )

    assert response.status_code == 422


def test_assistant_hides_project_from_outsider(client: FlaskClient) -> None:
    owner_token = register(client, "owner@example.com")
    outsider_token = register(client, "outsider@example.com")
    project_id = create_project(client, owner_token)

    response = client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"question": "What is this project?"},
        headers=auth(outsider_token),
    )

    assert response.status_code == 404


def test_assistant_does_not_invent_sources_without_retrieval(
    app: Flask, client: FlaskClient
) -> None:
    app.extensions["llm_provider"] = FakeLLMProvider()
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)

    response = client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"question": "What is this project?"},
        headers=auth(token),
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["message"]["sources"] == []


def test_assistant_reports_unconfigured_llm_provider(
    client: FlaskClient,
) -> None:
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)

    response = client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"question": "What is this project?"},
        headers=auth(token),
    )

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "AI_ASSISTANT_UNAVAILABLE"
