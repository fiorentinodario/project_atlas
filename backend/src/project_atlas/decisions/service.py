import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from project_atlas.ai_assistant.providers import LLMProvider, LLMProviderError
from project_atlas.decisions.schemas import DecisionData
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import ActivityLog, Document, Project, ProjectDecision, User
from project_atlas.models.enums import DecisionOrigin, DecisionStatus, ProjectRole
from project_atlas.projects.service import accessible_project
from project_atlas.rag.providers import EmbeddingProvider
from project_atlas.rag.retrieval import RetrievedChunk, retrieve_chunks
from project_atlas.tasks.service import WRITE_ROLES


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def serialize_decision(decision: ProjectDecision) -> dict:
    return {
        "id": str(decision.id),
        "project_id": str(decision.project_id),
        "title": decision.title,
        "description": decision.description,
        "decision_date": _iso(decision.decision_date),
        "origin": decision.origin.value,
        "status": decision.status.value,
        "source": (
            {
                "document_id": str(decision.source_document.id),
                "filename": decision.source_document.filename,
                "chunk_id": str(decision.source_chunk_id) if decision.source_chunk_id else None,
                "page_number": decision.source_page,
            }
            if decision.source_document
            else None
        ),
        "created_by": {
            "id": str(decision.created_by.id),
            "display_name": decision.created_by.display_name,
        },
        "confirmed_by": (
            {
                "id": str(decision.confirmed_by.id),
                "display_name": decision.confirmed_by.display_name,
            }
            if decision.confirmed_by
            else None
        ),
        "confirmed_at": _iso(decision.confirmed_at),
        "created_at": decision.created_at.isoformat(),
        "updated_at": decision.updated_at.isoformat(),
    }


def list_decisions(
    project_id: UUID,
    user_id: UUID,
    status: DecisionStatus | None = None,
) -> list[ProjectDecision]:
    accessible_project(project_id, user_id)
    statement = select(ProjectDecision).where(ProjectDecision.project_id == project_id)
    if status:
        statement = statement.where(ProjectDecision.status == status)
    return list(db.session.scalars(statement.order_by(ProjectDecision.decision_date.desc())))


def _source_document(project_id: UUID, document_id: UUID | None) -> Document | None:
    if document_id is None:
        return None
    document = db.session.get(Document, document_id)
    if document is None or document.project_id != project_id:
        raise ApiError("INVALID_DECISION_SOURCE", "Source document is not in this project.", 422)
    return document


def create_manual_decision(project: Project, data: DecisionData, actor: User) -> ProjectDecision:
    document = _source_document(project.id, data.source_document_id)
    if data.source_page is not None and document is None:
        raise ApiError("INVALID_DECISION_SOURCE", "A source page requires a document.", 422)
    decision = ProjectDecision(
        project=project,
        title=data.title,
        description=data.description,
        decision_date=data.decision_date or datetime.now(UTC),
        source_document=document,
        source_page=data.source_page,
        origin=DecisionOrigin.MANUAL,
        status=DecisionStatus.CONFIRMED,
        created_by=actor,
        confirmed_by=actor,
        confirmed_at=datetime.now(UTC),
    )
    db.session.add(decision)
    db.session.flush()
    _activity(decision, actor, "DECISION_CREATED")
    db.session.commit()
    return decision


def accessible_decision(
    decision_id: UUID, user_id: UUID, *, write: bool
) -> tuple[ProjectDecision, ProjectRole]:
    decision = db.session.get(ProjectDecision, decision_id)
    if decision is None:
        raise ApiError("DECISION_NOT_FOUND", "The requested decision does not exist.", 404)
    _project, role = accessible_project(
        decision.project_id, user_id, WRITE_ROLES if write else None
    )
    return decision, role


def update_decision(decision: ProjectDecision, data: DecisionData, actor: User) -> ProjectDecision:
    if "source_document_id" in data.provided_fields:
        decision.source_document = _source_document(decision.project_id, data.source_document_id)
        decision.source_chunk = None
        if decision.source_document is None and "source_page" not in data.provided_fields:
            decision.source_page = None
    resulting_page = (
        data.source_page if "source_page" in data.provided_fields else decision.source_page
    )
    if resulting_page is not None and decision.source_document is None:
        raise ApiError("INVALID_DECISION_SOURCE", "A source page requires a document.", 422)
    for field in ("title", "description", "decision_date", "source_page"):
        if field in data.provided_fields:
            setattr(decision, field, getattr(data, field))
    _activity(decision, actor, "DECISION_UPDATED")
    db.session.commit()
    return decision


def review_decision(
    decision: ProjectDecision, status: DecisionStatus, actor: User
) -> ProjectDecision:
    if (
        decision.origin is not DecisionOrigin.AI_DETECTED
        or decision.status is not DecisionStatus.PENDING
    ):
        raise ApiError("DECISION_NOT_PENDING", "Only pending AI decisions can be reviewed.", 409)
    decision.status = status
    if status is DecisionStatus.CONFIRMED:
        decision.confirmed_by = actor
        decision.confirmed_at = datetime.now(UTC)
    _activity(decision, actor, f"DECISION_{status.value}")
    db.session.commit()
    return decision


def delete_decision(decision: ProjectDecision, actor: User) -> None:
    _activity(decision, actor, "DECISION_DELETED")
    db.session.delete(decision)
    db.session.commit()


def _activity(decision: ProjectDecision, actor: User, action: str) -> None:
    db.session.add(
        ActivityLog(
            project_id=decision.project_id,
            actor=actor,
            action=action,
            entity_type="decision",
            entity_id=decision.id,
            activity_metadata={"decision_title": decision.title},
        )
    )


def _detection_prompt(chunks: list[RetrievedChunk]) -> str:
    context = "\n\n".join(
        f"[SOURCE {index}] {item.document.filename}, page {item.chunk.page_number or 'unknown'}\n"
        f"{item.chunk.content}"
        for index, item in enumerate(chunks, start=1)
    )
    return f"""Identify explicit project decisions already made in the source text.
Return only a JSON array with at most 10 objects. Each object must contain:
"title" (short string), "description" (string), and "source_number" (integer).
Do not include requirements, suggestions, questions, or decisions that are merely proposed.
If there are no explicit decisions, return [].

SOURCES
{context}"""


def _parse_detected(raw: str, chunks: list[RetrievedChunk]) -> list[dict]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    try:
        values = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise LLMProviderError("AI decision detection returned invalid JSON.") from error
    if not isinstance(values, list) or len(values) > 10:
        raise LLMProviderError("AI decision detection returned an invalid structure.")
    validated = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {"title", "description", "source_number"}:
            raise LLMProviderError("AI decision detection returned an invalid structure.")
        title, description, source_number = (
            value["title"],
            value["description"],
            value["source_number"],
        )
        if not isinstance(title, str) or not 2 <= len(title.strip()) <= 200:
            raise LLMProviderError("AI decision detection returned an invalid title.")
        if not isinstance(description, str) or not 2 <= len(description.strip()) <= 5000:
            raise LLMProviderError("AI decision detection returned an invalid description.")
        if not isinstance(source_number, int) or not 1 <= source_number <= len(chunks):
            raise LLMProviderError("AI decision detection returned an invalid source.")
        validated.append(
            {
                "title": title.strip(),
                "description": description.strip(),
                "source_number": source_number,
            }
        )
    return validated


def detect_decisions(
    project: Project,
    actor: User,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
) -> list[ProjectDecision]:
    chunks = retrieve_chunks(
        project.id,
        "confirmed project decisions choices selected technology approved changed abandoned",
        embedding_provider,
        limit=10,
    )
    if not chunks:
        raise ApiError("NO_DOCUMENT_CONTEXT", "No indexed document context is available.", 422)
    detected = _parse_detected(
        llm_provider.generate(
            "Extract only explicit project decisions. Return valid JSON and no commentary.",
            _detection_prompt(chunks),
        ),
        chunks,
    )
    existing_titles = {
        title.lower()
        for title in db.session.scalars(
            select(ProjectDecision.title).where(ProjectDecision.project_id == project.id)
        )
    }
    decisions = []
    for item in detected:
        if item["title"].lower() in existing_titles:
            continue
        source = chunks[item["source_number"] - 1]
        decision = ProjectDecision(
            project=project,
            title=item["title"],
            description=item["description"],
            decision_date=datetime.now(UTC),
            source_document=source.document,
            source_chunk=source.chunk,
            source_page=source.chunk.page_number,
            origin=DecisionOrigin.AI_DETECTED,
            status=DecisionStatus.PENDING,
            created_by=actor,
        )
        db.session.add(decision)
        decisions.append(decision)
        existing_titles.add(item["title"].lower())
    db.session.flush()
    for decision in decisions:
        _activity(decision, actor, "DECISION_AI_DETECTED")
    db.session.commit()
    return decisions
