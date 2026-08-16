from flask.testing import FlaskClient


def test_unknown_api_route_uses_standard_error_format(client: FlaskClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "The requested resource does not exist.",
        }
    }
