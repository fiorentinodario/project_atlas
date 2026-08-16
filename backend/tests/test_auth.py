from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import func, select
from werkzeug.security import check_password_hash

from project_atlas.extensions import db
from project_atlas.models import RefreshToken, User

REGISTER_PAYLOAD = {
    "display_name": "Dario Fiorentino",
    "email": "Dario@Example.com",
    "password": "securepass123",
}


def register(client: FlaskClient):
    return client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)


def csrf_header(client: FlaskClient) -> dict[str, str]:
    cookie = client.get_cookie("csrf_refresh_token")
    assert cookie is not None
    return {"X-CSRF-TOKEN": cookie.value}


def test_registration_hashes_password_and_returns_session(app: Flask, client: FlaskClient) -> None:
    response = register(client)

    assert response.status_code == 201
    payload = response.get_json()["data"]
    assert payload["user"]["email"] == "dario@example.com"
    assert payload["access_token"]
    assert "refresh_token_cookie=" in response.headers["Set-Cookie"]

    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "dario@example.com"))
        assert user is not None
        assert user.password_hash != REGISTER_PAYLOAD["password"]
        assert check_password_hash(user.password_hash, REGISTER_PAYLOAD["password"])
        assert db.session.scalar(select(func.count()).select_from(RefreshToken)) == 1


def test_registration_validates_external_input(client: FlaskClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"display_name": "D", "email": "invalid", "password": "short"},
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_email_is_rejected(client: FlaskClient) -> None:
    assert register(client).status_code == 201

    response = register(client)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_uses_generic_invalid_credentials_error(client: FlaskClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_current_user_requires_access_token(client: FlaskClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_current_user_returns_authenticated_profile(client: FlaskClient) -> None:
    access_token = register(client).get_json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["user"]["display_name"] == "Dario Fiorentino"


def test_refresh_rotates_stored_token(app: Flask, client: FlaskClient) -> None:
    register(client)

    response = client.post("/api/v1/auth/refresh", headers=csrf_header(client))

    assert response.status_code == 200
    assert response.get_json()["data"]["access_token"]
    with app.app_context():
        tokens = db.session.scalars(select(RefreshToken).order_by(RefreshToken.created_at)).all()
        assert len(tokens) == 2
        assert tokens[0].revoked_at is not None
        assert tokens[1].revoked_at is None


def test_logout_revokes_refresh_token_and_clears_cookie(app: Flask, client: FlaskClient) -> None:
    register(client)

    response = client.post("/api/v1/auth/logout", headers=csrf_header(client))

    assert response.status_code == 200
    assert any(
        "refresh_token_cookie=;" in header for header in response.headers.getlist("Set-Cookie")
    )
    with app.app_context():
        token = db.session.scalar(select(RefreshToken))
        assert token is not None
        assert token.revoked_at is not None
