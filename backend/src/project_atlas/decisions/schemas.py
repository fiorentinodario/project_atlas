from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from project_atlas.errors import ApiError


@dataclass(frozen=True)
class DecisionData:
    title: str | None
    description: str | None
    decision_date: datetime | None
    source_document_id: UUID | None
    source_page: int | None
    provided_fields: frozenset[str]


def _text(value: object, label: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        raise ApiError(
            "VALIDATION_ERROR",
            f"Decision {label} must contain {minimum} to {maximum} characters.",
            422,
        )
    return value.strip()


def _date(value: object) -> datetime:
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "Decision date must be an ISO 8601 datetime.", 422)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR", "Decision date must be an ISO 8601 datetime.", 422
        ) from error
    if parsed.tzinfo is None:
        raise ApiError("VALIDATION_ERROR", "Decision date must include a timezone.", 422)
    return parsed


def _uuid(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    try:
        return UUID(str(value))
    except ValueError as error:
        raise ApiError("VALIDATION_ERROR", "Source document id is invalid.", 422) from error


def _page(value: object) -> int | None:
    if value is None or value == "":
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ApiError("VALIDATION_ERROR", "Source page must be a positive integer.", 422)
    return value


def parse_decision(value: object, *, partial: bool) -> DecisionData:
    if not isinstance(value, dict):
        raise ApiError("INVALID_REQUEST", "A JSON object is required.", 400)
    allowed = {"title", "description", "decision_date", "source_document_id", "source_page"}
    if set(value) - allowed or (partial and not value):
        raise ApiError("VALIDATION_ERROR", "No supported decision fields were provided.", 422)
    if not partial and not {"title", "description"}.issubset(value):
        raise ApiError("VALIDATION_ERROR", "Decision title and description are required.", 422)
    return DecisionData(
        title=_text(value["title"], "title", 2, 200) if "title" in value else None,
        description=(
            _text(value["description"], "description", 2, 5000) if "description" in value else None
        ),
        decision_date=_date(value["decision_date"]) if "decision_date" in value else None,
        source_document_id=(
            _uuid(value.get("source_document_id")) if "source_document_id" in value else None
        ),
        source_page=_page(value.get("source_page")) if "source_page" in value else None,
        provided_fields=frozenset(value),
    )
