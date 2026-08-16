from datetime import UTC, datetime
from uuid import UUID

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select

from project_atlas.extensions import db
from project_atlas.models import Project, ProjectMember, Task, User
from project_atlas.models.enums import ProjectRole


def account(client: FlaskClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": email.split("@")[0].title(),
            "email": email,
            "password": "securepass123",
        },
    )
    return response.get_json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def project(client: FlaskClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Task project"},
        headers=auth(token),
    )
    return response.get_json()["data"]["project"]["id"]


def test_member_can_create_task_with_defaults(client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Build task API"},
        headers=auth(token),
    )

    assert response.status_code == 201
    task = response.get_json()["data"]["task"]
    assert task["status"] == "TODO"
    assert task["priority"] == "MEDIUM"
    assert task["source"] == "MANUAL"


def test_task_filters_and_search_are_project_scoped(client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)
    for payload in (
        {"title": "Build authentication", "priority": "HIGH"},
        {"title": "Write documentation", "status": "DONE"},
    ):
        client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json=payload,
            headers=auth(token),
        )

    filtered = client.get(
        f"/api/v1/projects/{project_id}/tasks?priority=HIGH&search=authentication",
        headers=auth(token),
    )

    assert filtered.status_code == 200
    items = filtered.get_json()["data"]["items"]
    assert [item["title"] for item in items] == ["Build authentication"]


def test_task_update_supports_status_priority_and_due_date(client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)
    created = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Ship release"},
        headers=auth(token),
    )
    task_id = created.get_json()["data"]["task"]["id"]
    due_date = datetime(2026, 9, 1, 12, tzinfo=UTC).isoformat()

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "DONE", "priority": "URGENT", "due_date": due_date},
        headers=auth(token),
    )

    assert response.status_code == 200
    task = response.get_json()["data"]["task"]
    assert task["status"] == "DONE"
    assert task["priority"] == "URGENT"
    assert task["due_date"] == due_date


def test_task_assignment_requires_project_membership(app: Flask, client: FlaskClient) -> None:
    owner_token = account(client, "owner@example.com")
    account(client, "outsider@example.com")
    project_id = project(client, owner_token)
    with app.app_context():
        outsider_id = db.session.scalar(select(User.id).where(User.email == "outsider@example.com"))

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Private task", "assigned_user_id": str(outsider_id)},
        headers=auth(owner_token),
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "INVALID_ASSIGNEE"


def test_viewer_can_read_but_cannot_write(app: Flask, client: FlaskClient) -> None:
    owner_token = account(client, "owner@example.com")
    viewer_token = account(client, "viewer@example.com")
    project_id = project(client, owner_token)
    with app.app_context():
        project_record = db.session.scalar(select(Project).where(Project.name == "Task project"))
        viewer = db.session.scalar(select(User).where(User.email == "viewer@example.com"))
        db.session.add(ProjectMember(project=project_record, user=viewer, role=ProjectRole.VIEWER))
        db.session.commit()

    read_response = client.get(f"/api/v1/projects/{project_id}/tasks", headers=auth(viewer_token))
    write_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Forbidden task"},
        headers=auth(viewer_token),
    )

    assert read_response.status_code == 200
    assert write_response.status_code == 403


def test_non_member_cannot_access_task_by_id(app: Flask, client: FlaskClient) -> None:
    owner_token = account(client, "owner@example.com")
    outsider_token = account(client, "outsider@example.com")
    project(client, owner_token)
    with app.app_context():
        owner = db.session.scalar(select(User).where(User.email == "owner@example.com"))
        project_record = db.session.scalar(select(Project).where(Project.name == "Task project"))
        task = Task(title="Secret", project=project_record, created_by=owner)
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "DONE"},
        headers=auth(outsider_token),
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_delete_task_removes_record(app: Flask, client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)
    created = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Disposable"},
        headers=auth(token),
    )
    task_id = created.get_json()["data"]["task"]["id"]

    response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth(token))

    assert response.status_code == 204
    with app.app_context():
        assert db.session.get(Task, UUID(task_id)) is None
