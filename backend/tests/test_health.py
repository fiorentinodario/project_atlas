from flask.testing import FlaskClient


def test_health_check_returns_service_status(client: FlaskClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "data": {
            "service": "project-atlas-api",
            "status": "healthy",
            "version": "0.1.0",
        }
    }


def test_health_check_allows_configured_frontend_origin(client: FlaskClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
