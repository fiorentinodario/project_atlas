import json
from uuid import UUID

from sqlalchemy import select

from project_atlas.ai_assistant.providers import LLMProvider, LLMProviderError
from project_atlas.extensions import db
from project_atlas.models import ActivityLog, AIAnalysis, Project, User
from project_atlas.models.enums import TaskPriority
from project_atlas.projects.service import accessible_project
from project_atlas.rag.providers import EmbeddingProvider, EmbeddingProviderError
from project_atlas.rag.retrieval import RetrievedChunk, retrieve_chunks

ANALYSIS_SYSTEM_PROMPT = """You are a rigorous project analyst.
Use only the supplied project data and document sources. Do not invent facts.
Return valid JSON matching the requested schema, without Markdown or commentary.
Use source numbers only when a statement is supported by that source.
Open questions should identify important missing or ambiguous information."""


def _source(item: RetrievedChunk, number: int) -> dict:
    return {
        "number": number,
        "chunk_id": str(item.chunk.id),
        "document_id": str(item.document.id),
        "filename": item.document.filename,
        "page_number": item.chunk.page_number,
        "excerpt": item.chunk.content[:320],
    }


def _analysis_prompt(project: Project, chunks: list[RetrievedChunk]) -> str:
    tasks = (
        "\n".join(
            f"- [{task.status.value}/{task.priority.value}] {task.title}: "
            f"{(task.description or 'No description')[:300]}"
            for task in project.tasks[:40]
        )
        or "No tasks"
    )
    decisions = (
        "\n".join(
            f"- {decision.title}: {decision.description[:500]}"
            for decision in project.decisions[:30]
            if decision.status.value == "CONFIRMED"
        )
        or "No confirmed decisions"
    )
    sources = (
        "\n\n".join(
            f"[SOURCE {index}] {item.document.filename}, page "
            f"{item.chunk.page_number or 'unknown'}\n{item.chunk.content}"
            for index, item in enumerate(chunks, start=1)
        )
        or "No indexed document sources"
    )
    return f"""Analyze this project and return exactly this JSON structure:
{{
  "summary": "string, 20-2000 characters",
  "requirements": [{{"text": "string", "source_numbers": [1]}}],
  "risks": [{{"text": "string", "severity": "LOW|MEDIUM|HIGH", "source_numbers": [1]}}],
  "open_questions": [{{"text": "string", "reason": "string"}}],
  "suggested_tasks": [{{
    "title": "string", "description": "string",
    "priority": "LOW|MEDIUM|HIGH|URGENT", "reason": "string", "source_numbers": [1]
  }}]
}}
Return at most 15 requirements, 10 risks, 10 open questions and 15 suggested tasks.
Use an empty source_numbers list for conclusions based only on project metadata, tasks or decisions.

PROJECT
Name: {project.name}
Description: {project.description or "No description"}
Status: {project.status.value}

TASKS
{tasks}

CONFIRMED DECISIONS
{decisions}

DOCUMENT SOURCES
{sources}"""


def _load_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise LLMProviderError("AI analysis returned invalid JSON.") from error
    if not isinstance(value, dict):
        raise LLMProviderError("AI analysis returned an invalid structure.")
    return value


def _text(value: object, label: str, minimum: int = 2, maximum: int = 2000) -> str:
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        raise LLMProviderError(f"AI analysis returned an invalid {label}.")
    return value.strip()


def _sources(value: object, chunks: list[RetrievedChunk]) -> list[dict]:
    if not isinstance(value, list) or len(value) > len(chunks):
        raise LLMProviderError("AI analysis returned invalid source references.")
    if any(not isinstance(number, int) or isinstance(number, bool) for number in value):
        raise LLMProviderError("AI analysis returned invalid source references.")
    unique_numbers = list(dict.fromkeys(value))
    if any(number < 1 or number > len(chunks) for number in unique_numbers):
        raise LLMProviderError("AI analysis returned invalid source references.")
    return [_source(chunks[number - 1], number) for number in unique_numbers]


def _validate_items(value: object, limit: int, fields: set[str], label: str) -> list[dict]:
    if not isinstance(value, list) or len(value) > limit:
        raise LLMProviderError(f"AI analysis returned invalid {label}.")
    if any(not isinstance(item, dict) or set(item) != fields for item in value):
        raise LLMProviderError(f"AI analysis returned invalid {label}.")
    return value


def _validate_analysis(value: dict, chunks: list[RetrievedChunk]) -> dict:
    expected = {"summary", "requirements", "risks", "open_questions", "suggested_tasks"}
    if set(value) != expected:
        raise LLMProviderError("AI analysis returned an invalid structure.")
    requirements = [
        {
            "text": _text(item["text"], "requirement"),
            "sources": _sources(item["source_numbers"], chunks),
        }
        for item in _validate_items(
            value["requirements"], 15, {"text", "source_numbers"}, "requirements"
        )
    ]
    risks = []
    for item in _validate_items(
        value["risks"], 10, {"text", "severity", "source_numbers"}, "risks"
    ):
        if item["severity"] not in {"LOW", "MEDIUM", "HIGH"}:
            raise LLMProviderError("AI analysis returned an invalid risk severity.")
        risks.append(
            {
                "text": _text(item["text"], "risk"),
                "severity": item["severity"],
                "sources": _sources(item["source_numbers"], chunks),
            }
        )
    open_questions = [
        {
            "text": _text(item["text"], "open question"),
            "reason": _text(item["reason"], "open question reason"),
        }
        for item in _validate_items(
            value["open_questions"], 10, {"text", "reason"}, "open questions"
        )
    ]
    suggested_tasks = []
    for item in _validate_items(
        value["suggested_tasks"],
        15,
        {"title", "description", "priority", "reason", "source_numbers"},
        "suggested tasks",
    ):
        try:
            priority = TaskPriority(item["priority"])
        except (TypeError, ValueError) as error:
            raise LLMProviderError("AI analysis returned an invalid task priority.") from error
        suggested_tasks.append(
            {
                "title": _text(item["title"], "task title", maximum=200),
                "description": _text(item["description"], "task description", maximum=5000),
                "priority": priority.value,
                "reason": _text(item["reason"], "task reason"),
                "sources": _sources(item["source_numbers"], chunks),
            }
        )
    return {
        "summary": _text(value["summary"], "summary", minimum=20),
        "requirements": requirements,
        "risks": risks,
        "open_questions": open_questions,
        "suggested_tasks": suggested_tasks,
    }


def serialize_analysis(analysis: AIAnalysis) -> dict:
    return {
        "id": str(analysis.id),
        "project_id": str(analysis.project_id),
        "summary": analysis.summary,
        "requirements": analysis.requirements,
        "risks": analysis.risks,
        "open_questions": analysis.open_questions,
        "suggested_tasks": analysis.suggested_tasks,
        "provider": analysis.provider,
        "model": analysis.model,
        "requested_by": {
            "id": str(analysis.requested_by.id),
            "display_name": analysis.requested_by.display_name,
        },
        "created_at": analysis.created_at.isoformat(),
    }


def latest_analysis(project_id: UUID, user_id: UUID) -> AIAnalysis | None:
    accessible_project(project_id, user_id)
    return db.session.scalar(
        select(AIAnalysis)
        .where(AIAnalysis.project_id == project_id)
        .order_by(AIAnalysis.created_at.desc())
        .limit(1)
    )


def analyze_project(
    project: Project,
    actor: User,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
) -> AIAnalysis:
    try:
        chunks = retrieve_chunks(
            project.id,
            "project requirements risks constraints unknowns decisions deliverables",
            embedding_provider,
            limit=15,
        )
    except EmbeddingProviderError:
        chunks = []
    validated = _validate_analysis(
        _load_json(
            llm_provider.generate(ANALYSIS_SYSTEM_PROMPT, _analysis_prompt(project, chunks))
        ),
        chunks,
    )
    analysis = AIAnalysis(
        project=project,
        requested_by=actor,
        summary=validated["summary"],
        requirements=validated["requirements"],
        risks=validated["risks"],
        open_questions=validated["open_questions"],
        suggested_tasks=validated["suggested_tasks"],
        provider=llm_provider.name,
        model=llm_provider.model,
    )
    db.session.add(analysis)
    db.session.flush()
    db.session.add(
        ActivityLog(
            project=project,
            actor=actor,
            action="AI_ANALYSIS_COMPLETED",
            entity_type="ai_analysis",
            entity_id=analysis.id,
            activity_metadata={
                "requirements": len(analysis.requirements),
                "risks": len(analysis.risks),
                "suggested_tasks": len(analysis.suggested_tasks),
            },
        )
    )
    db.session.commit()
    return analysis
