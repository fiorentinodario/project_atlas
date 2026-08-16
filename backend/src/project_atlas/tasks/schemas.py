from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from project_atlas.errors import ApiError
from project_atlas.models.enums import TaskPriority, TaskStatus


@dataclass(frozen=True)
class TaskData:
    title: str | None
    description: str | None
    status: TaskStatus | None
    priority: TaskPriority | None
    due_date: datetime | None
    assigned_user_id: UUID | None
    provided_fields: frozenset[str]


def _payload(value: object) -> dict:
    if not isinstance(value, dict):
        raise ApiError("INVALID_REQUEST", "A JSON object is required.", 400)
    return value


def _title(value: object) -> str:
    if not isinstance(value, str) or not 2 <= len(value.strip()) <= 200:
        raise ApiError("VALIDATION_ERROR", "Task title must contain 2 to 200 characters.", 422)
    return value.strip()


def _description(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or len(value.strip()) > 5000:
        raise ApiError("VALIDATION_ERROR", "Task description must not exceed 5000 characters.", 422)
    return value.strip()


def _enum(value: object, enum_type, label: str):
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        raise ApiError("VALIDATION_ERROR", f"Task {label} is invalid.", 422) from error


def _due_date(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "Task due date must be an ISO 8601 datetime.", 422)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR", "Task due date must be an ISO 8601 datetime.", 422
        ) from error
    if parsed.tzinfo is None:
        raise ApiError("VALIDATION_ERROR", "Task due date must include a timezone.", 422)
    return parsed


def _assigned_user(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    try:
        return UUID(str(value))
    except ValueError as error:
        raise ApiError("VALIDATION_ERROR", "Assigned user id is invalid.", 422) from error


def parse_task(value: object, *, partial: bool) -> TaskData:
    data = _payload(value)
    allowed = {"title", "description", "status", "priority", "due_date", "assigned_user_id"}
    if set(data) - allowed or (partial and not data):
        raise ApiError("VALIDATION_ERROR", "No supported task fields were provided.", 422)
    if not partial and "title" not in data:
        raise ApiError("VALIDATION_ERROR", "Task title is required.", 422)

    return TaskData(
        title=_title(data["title"]) if "title" in data else None,
        description=_description(data.get("description")) if "description" in data else None,
        status=_enum(data["status"], TaskStatus, "status") if "status" in data else None,
        priority=(
            _enum(data["priority"], TaskPriority, "priority") if "priority" in data else None
        ),
        due_date=_due_date(data.get("due_date")) if "due_date" in data else None,
        assigned_user_id=(
            _assigned_user(data.get("assigned_user_id")) if "assigned_user_id" in data else None
        ),
        provided_fields=frozenset(data),
    )
