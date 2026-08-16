from io import BytesIO

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select

from project_atlas.extensions import db
from project_atlas.models import Project, ProjectDecision, ProjectMember, User
from project_atlas.models.enums import DecisionOrigin, DecisionStatus, ProjectRole


class FakeEmbeddingProvider:
    dimensions = 1536

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for _ in texts:
            vector = [0.0] * self.dimensions
            vector[0] = 1.0
            vectors.append(vector)
        return vectors


class FakeDecisionProvider:
    name = "fake"
    model = "fake-model"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        assert "explicit project decisions" in user_prompt
        return """[
          {"title": "PostgreSQL selected",
           "description": "The team selected PostgreSQL as the primary database.",
           "source_number": 1}
        ]"""


def register(client: FlaskClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"display_name": email.split("@")[0], "email": email, "password": "securepass123"},
    )
    return response.get_json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_project(client: FlaskClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects", json={"name": "Decision project"}, headers=auth(token)
    )
    return response.get_json()["data"]["project"]["id"]


def test_manual_decision_crud(app: Flask, client: FlaskClient) -> None:
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)

    created = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={
            "title": "Use PostgreSQL",
            "description": "PostgreSQL will be the primary database.",
            "decision_date": "2026-08-16T10:00:00Z",
        },
        headers=auth(token),
    )

    assert created.status_code == 201
    decision = created.get_json()["data"]["decision"]
    assert decision["origin"] == "MANUAL"
    assert decision["status"] == "CONFIRMED"
    assert decision["confirmed_by"]["display_name"] == "owner"

    updated = client.patch(
        f"/api/v1/decisions/{decision['id']}",
        json={"description": "PostgreSQL with pgvector will be used."},
        headers=auth(token),
    )
    listing = client.get(f"/api/v1/projects/{project_id}/decisions", headers=auth(token))
    deleted = client.delete(f"/api/v1/decisions/{decision['id']}", headers=auth(token))

    assert updated.status_code == 200
    assert listing.get_json()["data"]["items"][0]["description"].endswith("will be used.")
    assert deleted.status_code == 204
    with app.app_context():
        assert db.session.scalar(select(ProjectDecision)) is None


def test_viewer_can_list_but_cannot_create(app: Flask, client: FlaskClient) -> None:
    owner_token = register(client, "owner@example.com")
    viewer_token = register(client, "viewer@example.com")
    project_id = create_project(client, owner_token)
    with app.app_context():
        project = db.session.scalar(select(Project))
        viewer = db.session.scalar(select(User).where(User.email == "viewer@example.com"))
        db.session.add(ProjectMember(project=project, user=viewer, role=ProjectRole.VIEWER))
        db.session.commit()

    listing = client.get(f"/api/v1/projects/{project_id}/decisions", headers=auth(viewer_token))
    creating = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={"title": "A decision", "description": "A confirmed choice"},
        headers=auth(viewer_token),
    )

    assert listing.status_code == 200
    assert creating.status_code == 403


def test_ai_detection_requires_human_confirmation(app: Flask, client: FlaskClient) -> None:
    app.extensions["embedding_provider"] = FakeEmbeddingProvider()
    app.extensions["llm_provider"] = FakeDecisionProvider()
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)
    upload = client.post(
        f"/api/v1/projects/{project_id}/documents",
        data={
            "file": (
                BytesIO(b"The team selected PostgreSQL as the primary database."),
                "meeting-notes.txt",
                "text/plain",
            )
        },
        headers=auth(token),
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201

    detected = client.post(f"/api/v1/projects/{project_id}/decisions/detect", headers=auth(token))

    assert detected.status_code == 201
    decision = detected.get_json()["data"]["items"][0]
    assert decision["origin"] == "AI_DETECTED"
    assert decision["status"] == "PENDING"
    assert decision["source"]["filename"] == "meeting-notes.txt"
    assert decision["source"]["page_number"] == 1

    confirmed = client.post(f"/api/v1/decisions/{decision['id']}/confirm", headers=auth(token))
    repeated = client.post(f"/api/v1/decisions/{decision['id']}/confirm", headers=auth(token))

    assert confirmed.status_code == 200
    assert confirmed.get_json()["data"]["decision"]["status"] == "CONFIRMED"
    assert repeated.status_code == 409
    with app.app_context():
        record = db.session.scalar(select(ProjectDecision))
        assert record.origin is DecisionOrigin.AI_DETECTED
        assert record.status is DecisionStatus.CONFIRMED


def test_source_page_requires_project_document(client: FlaskClient) -> None:
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)

    response = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={"title": "A decision", "description": "A confirmed choice", "source_page": 2},
        headers=auth(token),
    )

    assert response.status_code == 422
