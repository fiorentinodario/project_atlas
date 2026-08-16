from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import ActivityLog, AIAnalysis, Task, User
from project_atlas.models.enums import TaskPriority, TaskSource, TaskStatus
from project_atlas.projects.service import accessible_project
from project_atlas.tasks.service import WRITE_ROLES


def parse_suggestion_indices(value: object) -> list[int]:
    if not isinstance(value, dict) or set(value) != {"suggestion_indices"}:
        raise ApiError("INVALID_REQUEST", "Suggestion indices are required.", 400)
    indices = value["suggestion_indices"]
    if not isinstance(indices, list) or not 1 <= len(indices) <= 15:
        raise ApiError("VALIDATION_ERROR", "Select between 1 and 15 suggested tasks.", 422)
    if any(not isinstance(index, int) or isinstance(index, bool) or index < 0 for index in indices):
        raise ApiError("VALIDATION_ERROR", "Suggestion indices must be non-negative integers.", 422)
    if len(set(indices)) != len(indices):
        raise ApiError("VALIDATION_ERROR", "Each suggested task can be selected only once.", 422)
    return indices


def accessible_analysis(analysis_id: UUID, user_id: UUID) -> AIAnalysis:
    analysis = db.session.get(AIAnalysis, analysis_id)
    if analysis is None:
        raise ApiError("ANALYSIS_NOT_FOUND", "The requested analysis does not exist.", 404)
    accessible_project(analysis.project_id, user_id, WRITE_ROLES)
    return analysis


def create_tasks_from_suggestions(
    analysis: AIAnalysis,
    indices: list[int],
    actor: User,
) -> list[Task]:
    suggestions = analysis.suggested_tasks
    if any(index >= len(suggestions) for index in indices):
        raise ApiError("INVALID_SUGGESTION", "A selected task suggestion does not exist.", 422)
    existing = set(
        db.session.scalars(
            select(Task.source_suggestion_index).where(
                Task.source_analysis_id == analysis.id,
                Task.source_suggestion_index.in_(indices),
            )
        )
    )
    if existing:
        raise ApiError(
            "SUGGESTION_ALREADY_CREATED",
            "One or more selected suggestions have already been converted to tasks.",
            409,
        )
    tasks = []
    for index in indices:
        suggestion = suggestions[index]
        task = Task(
            project_id=analysis.project_id,
            title=suggestion["title"],
            description=suggestion["description"],
            status=TaskStatus.TODO,
            priority=TaskPriority(suggestion["priority"]),
            created_by=actor,
            source=TaskSource.AI_GENERATED,
            source_analysis_id=analysis.id,
            source_suggestion_index=index,
        )
        db.session.add(task)
        tasks.append(task)
    try:
        db.session.flush()
    except IntegrityError as error:
        db.session.rollback()
        raise ApiError(
            "SUGGESTION_ALREADY_CREATED",
            "A selected suggestion was converted by another request.",
            409,
        ) from error
    db.session.add(
        ActivityLog(
            project_id=analysis.project_id,
            actor=actor,
            action="AI_TASKS_CREATED",
            entity_type="ai_analysis",
            entity_id=analysis.id,
            activity_metadata={
                "count": len(tasks),
                "task_ids": [str(task.id) for task in tasks],
            },
        )
    )
    db.session.commit()
    return tasks
