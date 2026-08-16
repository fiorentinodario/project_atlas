from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email

from project_atlas.errors import ApiError


@dataclass(frozen=True)
class RegistrationData:
    email: str
    password: str
    display_name: str


@dataclass(frozen=True)
class LoginData:
    email: str
    password: str


def _object_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ApiError("INVALID_REQUEST", "A JSON object is required.", 400)
    return payload


def _email(value: object) -> str:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "A valid email address is required.", 422)
    try:
        return validate_email(value, check_deliverability=False).normalized.lower()
    except EmailNotValidError as error:
        raise ApiError("VALIDATION_ERROR", "A valid email address is required.", 422) from error


def _password(value: object) -> str:
    if not isinstance(value, str) or len(value) < 12 or len(value) > 128:
        raise ApiError(
            "VALIDATION_ERROR",
            "Password must contain between 12 and 128 characters.",
            422,
        )
    if not any(character.isalpha() for character in value) or not any(
        character.isdigit() for character in value
    ):
        raise ApiError(
            "VALIDATION_ERROR",
            "Password must contain at least one letter and one number.",
            422,
        )
    return value


def parse_registration(payload: object) -> RegistrationData:
    data = _object_payload(payload)
    display_name = data.get("display_name")
    if not isinstance(display_name, str) or not 2 <= len(display_name.strip()) <= 120:
        raise ApiError(
            "VALIDATION_ERROR",
            "Display name must contain between 2 and 120 characters.",
            422,
        )
    return RegistrationData(
        email=_email(data.get("email")),
        password=_password(data.get("password")),
        display_name=display_name.strip(),
    )


def parse_login(payload: object) -> LoginData:
    data = _object_payload(payload)
    password = data.get("password")
    if not isinstance(password, str):
        raise ApiError("VALIDATION_ERROR", "Email and password are required.", 422)
    return LoginData(email=_email(data.get("email")), password=password)
