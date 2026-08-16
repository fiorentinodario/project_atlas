from dataclasses import dataclass

from project_atlas.errors import ApiError
from project_atlas.models.enums import ProjectStatus


@dataclass(frozen=True)
class ProjectCreateData:
    name: str
    description: str | None


@dataclass(frozen=True)
class ProjectUpdateData:
    name: str | None = None
    description: str | None = None
    description_provided: bool = False
    status: ProjectStatus | None = None


def _payload(value: object) -> dict:
    if not isinstance(value, dict):
        raise ApiError("INVALID_REQUEST", "A JSON object is required.", 400)
    return value


def _name(value: object) -> str:
    if not isinstance(value, str) or not 2 <= len(value.strip()) <= 160:
        raise ApiError(
            "VALIDATION_ERROR",
            "Project name must contain between 2 and 160 characters.",
            422,
        )
    return value.strip()


def _description(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or len(value.strip()) > 2000:
        raise ApiError(
            "VALIDATION_ERROR",
            "Project description must not exceed 2000 characters.",
            422,
        )
    return value.strip()


def parse_project_create(value: object) -> ProjectCreateData:
    data = _payload(value)
    unknown_fields = set(data) - {"name", "description"}
    if unknown_fields:
        raise ApiError("VALIDATION_ERROR", "The request contains unsupported fields.", 422)
    return ProjectCreateData(
        name=_name(data.get("name")),
        description=_description(data.get("description")),
    )


def parse_project_update(value: object) -> ProjectUpdateData:
    data = _payload(value)
    allowed_fields = {"name", "description", "status"}
    if not data or set(data) - allowed_fields:
        raise ApiError("VALIDATION_ERROR", "No supported project fields were provided.", 422)

    status = None
    if "status" in data:
        try:
            status = ProjectStatus(data["status"])
        except (TypeError, ValueError) as error:
            raise ApiError("VALIDATION_ERROR", "Project status is invalid.", 422) from error

    return ProjectUpdateData(
        name=_name(data["name"]) if "name" in data else None,
        description=_description(data["description"]) if "description" in data else None,
        description_provided="description" in data,
        status=status,
    )
