from flask.testing import FlaskClient

from project_atlas import create_app


def register(client: FlaskClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Dashboard User",
            "email": "dashboard@example.com",
            "password": "securepass123",
        },
    )
    return response.get_json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_aggregates_authorized_project_data(client: FlaskClient) -> None:
    token = register(client)
    project = client.post(
        "/api/v1/projects",
        json={"name": "Dashboard project"},
        headers=auth(token),
    ).get_json()["data"]["project"]
    client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "In progress task", "status": "IN_PROGRESS"},
        headers=auth(token),
    )
    client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Completed task", "status": "DONE"},
        headers=auth(token),
    )

    response = client.get("/api/v1/dashboard", headers=auth(token))

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["stats"] == {
        "active_projects": 1,
        "total_tasks": 2,
        "tasks_in_progress": 1,
        "completed_tasks": 1,
    }
    assert data["recent_projects"][0]["progress"] == 50
    assert data["recent_activity"][0]["project"]["name"] == "Dashboard project"


def test_api_responses_include_security_headers(client: FlaskClient) -> None:
    response = client.get("/api/v1/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_production_responses_enable_hsts(tmp_path) -> None:
    app = create_app(
        "production",
        {
            "SECRET_KEY": "production-test-secret",
            "JWT_SECRET_KEY": "production-test-jwt-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite+pysqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {},
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        },
    )

    response = app.test_client().get("/api/v1/health")

    assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")
