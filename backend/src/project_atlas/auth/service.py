import hashlib
from datetime import UTC, datetime
from uuid import UUID

from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from project_atlas.auth.schemas import LoginData, RegistrationData
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import RefreshToken, User


def _hash_token_identifier(identifier: str) -> str:
    return hashlib.sha256(identifier.encode()).hexdigest()


def serialize_user(user: User) -> dict[str, str]:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
    }


def register_user(data: RegistrationData) -> User:
    existing_user = db.session.scalar(select(User).where(User.email == data.email))
    if existing_user:
        raise ApiError("EMAIL_ALREADY_REGISTERED", "An account already uses this email.", 409)

    user = User(
        email=data.email,
        display_name=data.display_name,
        password_hash=generate_password_hash(data.password, method="scrypt"),
    )
    db.session.add(user)
    try:
        db.session.flush()
    except IntegrityError as error:
        db.session.rollback()
        raise ApiError(
            "EMAIL_ALREADY_REGISTERED", "An account already uses this email.", 409
        ) from error
    return user


def authenticate_user(data: LoginData) -> User:
    user = db.session.scalar(select(User).where(User.email == data.email))
    if (
        user is None
        or not user.is_active
        or not check_password_hash(user.password_hash, data.password)
    ):
        raise ApiError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
    return user


def issue_token_pair(user: User) -> tuple[str, str]:
    identity = str(user.id)
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    decoded_refresh = decode_token(refresh_token)
    stored_token = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token_identifier(decoded_refresh["jti"]),
        expires_at=datetime.fromtimestamp(decoded_refresh["exp"], tz=UTC),
    )
    db.session.add(stored_token)
    db.session.commit()
    return access_token, refresh_token


def rotate_refresh_token(user_id: str, token_identifier: str) -> tuple[str, str]:
    stored_token = db.session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == _hash_token_identifier(token_identifier),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if stored_token is None or stored_token.user_id != UUID(user_id):
        raise ApiError("TOKEN_REVOKED", "The refresh token is no longer valid.", 401)

    user = db.session.get(User, UUID(user_id))
    if user is None or not user.is_active:
        raise ApiError("USER_NOT_AVAILABLE", "The user account is not available.", 401)

    stored_token.revoked_at = datetime.now(UTC)
    db.session.flush()
    return issue_token_pair(user)


def revoke_refresh_token(token_identifier: str) -> None:
    stored_token = db.session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == _hash_token_identifier(token_identifier),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if stored_token:
        stored_token.revoked_at = datetime.now(UTC)
        db.session.commit()
