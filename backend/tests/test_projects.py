from uuid import UUID

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import func, select

from project_atlas.extensions import db
from project_atlas.models import ActivityLog, Project, ProjectMember, User
from project_atlas.models.enums import ProjectRole


def create_account(client: FlaskClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": email.split("@")[0].title(),
            "email": email,
            "password": "securepass123",
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["access_token"]


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_project_creation_is_atomic_and_assigns_owner(app: Flask, client: FlaskClient) -> None:
    token = create_account(client, "owner@example.com")

    response = client.post(
        "/api/v1/projects",
        json={"name": "Project Atlas", "description": "Knowledge platform"},
        headers=authorization(token),
    )

    assert response.status_code == 201
    project_payload = response.get_json()["data"]["project"]
    assert project_payload["role"] == "OWNER"
    assert project_payload["status"] == "ACTIVE"
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(Project)) == 1
        member = db.session.scalar(select(ProjectMember))
        assert member is not None and member.role is ProjectRole.OWNER
        assert db.session.scalar(select(ActivityLog.action)) == "PROJECT_CREATED"


def test_project_list_only_returns_memberships(client: FlaskClient) -> None:
    first_token = create_account(client, "first@example.com")
    second_token = create_account(client, "second@example.com")
    client.post(
        "/api/v1/projects",
        json={"name": "Private project"},
        headers=authorization(first_token),
    )

    response = client.get("/api/v1/projects", headers=authorization(second_token))

    assert response.status_code == 200
    assert response.get_json()["data"]["items"] == []


def test_non_member_cannot_discover_project(client: FlaskClient) -> None:
    owner_token = create_account(client, "owner@example.com")
    outsider_token = create_account(client, "outsider@example.com")
    created = client.post(
        "/api/v1/projects",
        json={"name": "Hidden roadmap"},
        headers=authorization(owner_token),
    )
    project_id = created.get_json()["data"]["project"]["id"]

    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers=authorization(outsider_token),
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_member_cannot_update_or_delete_project(app: Flask, client: FlaskClient) -> None:
    owner_token = create_account(client, "owner@example.com")
    member_token = create_account(client, "member@example.com")
    created = client.post(
        "/api/v1/projects",
        json={"name": "Shared project"},
        headers=authorization(owner_token),
    )
    project_id = created.get_json()["data"]["project"]["id"]
    with app.app_context():
        project = db.session.get(Project, UUID(project_id))
        member_id = db.session.scalar(select(User.id).where(User.email == "member@example.com"))
        assert project is not None and member_id is not None
        db.session.add(
            ProjectMember(project_id=project.id, user_id=member_id, role=ProjectRole.MEMBER)
        )
        db.session.commit()

    update_response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Unauthorized change"},
        headers=authorization(member_token),
    )
    delete_response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=authorization(member_token),
    )

    assert update_response.status_code == 403
    assert delete_response.status_code == 403


def test_owner_can_update_without_clearing_omitted_description(client: FlaskClient) -> None:
    token = create_account(client, "owner@example.com")
    created = client.post(
        "/api/v1/projects",
        json={"name": "Original", "description": "Keep me"},
        headers=authorization(token),
    )
    project_id = created.get_json()["data"]["project"]["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated"},
        headers=authorization(token),
    )

    assert response.status_code == 200
    project = response.get_json()["data"]["project"]
    assert project["name"] == "Updated"
    assert project["description"] == "Keep me"


def test_owner_can_delete_project(client: FlaskClient) -> None:
    token = create_account(client, "owner@example.com")
    created = client.post(
        "/api/v1/projects",
        json={"name": "Temporary"},
        headers=authorization(token),
    )
    project_id = created.get_json()["data"]["project"]["id"]

    response = client.delete(f"/api/v1/projects/{project_id}", headers=authorization(token))

    assert response.status_code == 204
    missing = client.get(f"/api/v1/projects/{project_id}", headers=authorization(token))
    assert missing.status_code == 404
