import json
from io import BytesIO

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import func, select

from project_atlas.extensions import db
from project_atlas.models import ActivityLog, AIAnalysis, Project, ProjectMember, User
from project_atlas.models.enums import ProjectRole


class FakeEmbeddingProvider:
    dimensions = 1536

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for _ in texts:
            vector = [0.0] * self.dimensions
            vector[0] = 1.0
            vectors.append(vector)
        return vectors


class FakeAnalysisProvider:
    name = "fake"
    model = "fake-analysis-model"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        assert "rigorous project analyst" in system_prompt
        assert "requirements.txt" in user_prompt
        return json.dumps(
            {
                "summary": "ProjectAtlas is a secure project knowledge platform.",
                "requirements": [
                    {"text": "Users must authenticate with JWT.", "source_numbers": [1]}
                ],
                "risks": [
                    {
                        "text": "Token rotation details are incomplete.",
                        "severity": "MEDIUM",
                        "source_numbers": [1],
                    }
                ],
                "open_questions": [
                    {
                        "text": "What is the final launch date?",
                        "reason": "No release deadline is documented.",
                    }
                ],
                "suggested_tasks": [
                    {
                        "title": "Document token rotation",
                        "description": "Define refresh token rotation behavior.",
                        "priority": "HIGH",
                        "reason": "Authentication details are incomplete.",
                        "source_numbers": [1],
                    }
                ],
            }
        )


class InvalidAnalysisProvider:
    name = "fake"
    model = "invalid-model"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return '{"summary": "Incomplete"}'


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
        "/api/v1/projects",
        json={"name": "Analysis project", "description": "A knowledge platform"},
        headers=auth(token),
    )
    return response.get_json()["data"]["project"]["id"]


def upload_document(client: FlaskClient, project_id: str, token: str) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents",
        data={
            "file": (
                BytesIO(b"Users must authenticate with short-lived JWT access tokens."),
                "requirements.txt",
                "text/plain",
            )
        },
        headers=auth(token),
        content_type="multipart/form-data",
    )
    assert response.status_code == 201


def test_analysis_is_validated_persisted_and_retrievable(app: Flask, client: FlaskClient) -> None:
    app.extensions["embedding_provider"] = FakeEmbeddingProvider()
    app.extensions["llm_provider"] = FakeAnalysisProvider()
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)
    upload_document(client, project_id, token)

    created = client.post(f"/api/v1/projects/{project_id}/analyses", headers=auth(token))

    assert created.status_code == 201
    analysis = created.get_json()["data"]["analysis"]
    assert analysis["provider"] == "fake"
    assert analysis["requirements"][0]["sources"][0]["filename"] == "requirements.txt"
    assert analysis["risks"][0]["severity"] == "MEDIUM"
    assert analysis["suggested_tasks"][0]["priority"] == "HIGH"

    latest = client.get(f"/api/v1/projects/{project_id}/analyses/latest", headers=auth(token))
    assert latest.status_code == 200
    assert latest.get_json()["data"]["analysis"]["id"] == analysis["id"]
    with app.app_context():
        assert db.session.scalar(select(func.count(AIAnalysis.id))) == 1
        activity = db.session.scalar(
            select(ActivityLog).where(ActivityLog.action == "AI_ANALYSIS_COMPLETED")
        )
        assert activity.activity_metadata["suggested_tasks"] == 1


def test_invalid_ai_structure_is_not_persisted(app: Flask, client: FlaskClient) -> None:
    app.extensions["llm_provider"] = InvalidAnalysisProvider()
    token = register(client, "owner@example.com")
    project_id = create_project(client, token)

    response = client.post(f"/api/v1/projects/{project_id}/analyses", headers=auth(token))

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "AI_ANALYSIS_FAILED"
    with app.app_context():
        assert db.session.scalar(select(func.count(AIAnalysis.id))) == 0


def test_viewer_can_read_but_cannot_run_analysis(app: Flask, client: FlaskClient) -> None:
    owner_token = register(client, "owner@example.com")
    viewer_token = register(client, "viewer@example.com")
    project_id = create_project(client, owner_token)
    with app.app_context():
        project = db.session.scalar(select(Project))
        viewer = db.session.scalar(select(User).where(User.email == "viewer@example.com"))
        db.session.add(ProjectMember(project=project, user=viewer, role=ProjectRole.VIEWER))
        db.session.commit()

    reading = client.get(
        f"/api/v1/projects/{project_id}/analyses/latest", headers=auth(viewer_token)
    )
    running = client.post(f"/api/v1/projects/{project_id}/analyses", headers=auth(viewer_token))

    assert reading.status_code == 200
    assert reading.get_json()["data"]["analysis"] is None
    assert running.status_code == 403
