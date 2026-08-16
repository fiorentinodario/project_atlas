from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select

from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import ActivityLog, Project, ProjectMember, Task, User
from project_atlas.models.enums import ProjectRole, TaskPriority, TaskStatus
from project_atlas.projects.service import accessible_project
from project_atlas.tasks.schemas import TaskData

WRITE_ROLES = {ProjectRole.OWNER, ProjectRole.ADMIN, ProjectRole.MEMBER}


def _iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def serialize_task(task: Task) -> dict:
    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "due_date": _iso_datetime(task.due_date),
        "assigned_user": (
            {
                "id": str(task.assigned_user.id),
                "display_name": task.assigned_user.display_name,
            }
            if task.assigned_user
            else None
        ),
        "created_by": {
            "id": str(task.created_by.id),
            "display_name": task.created_by.display_name,
        },
        "source": task.source.value,
        "source_analysis_id": str(task.source_analysis_id) if task.source_analysis_id else None,
        "source_suggestion_index": task.source_suggestion_index,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _validate_assignee(project_id: UUID, assigned_user_id: UUID | None) -> None:
    if assigned_user_id is None:
        return
    membership = db.session.scalar(
        select(ProjectMember.id).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == assigned_user_id,
        )
    )
    if membership is None:
        raise ApiError("INVALID_ASSIGNEE", "The assignee is not a project member.", 422)


def list_tasks(
    project_id: UUID,
    user_id: UUID,
    page: int,
    per_page: int,
    status: TaskStatus | None,
    priority: TaskPriority | None,
    search: str | None,
):
    accessible_project(project_id, user_id)
    statement = select(Task).where(Task.project_id == project_id)
    if status:
        statement = statement.where(Task.status == status)
    if priority:
        statement = statement.where(Task.priority == priority)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))
    return db.paginate(
        statement.order_by(Task.created_at.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )


def create_task(project: Project, data: TaskData, actor: User) -> Task:
    _validate_assignee(project.id, data.assigned_user_id)
    task = Task(
        project=project,
        title=data.title,
        description=data.description,
        status=data.status or TaskStatus.TODO,
        priority=data.priority or TaskPriority.MEDIUM,
        due_date=data.due_date,
        assigned_user_id=data.assigned_user_id,
        created_by=actor,
    )
    db.session.add(task)
    db.session.flush()
    db.session.add(
        ActivityLog(
            project=project,
            actor=actor,
            action="TASK_CREATED",
            entity_type="task",
            entity_id=task.id,
            activity_metadata={"task_title": task.title},
        )
    )
    db.session.commit()
    return task


def accessible_task(task_id: UUID, user_id: UUID, *, write: bool) -> tuple[Task, ProjectRole]:
    task = db.session.get(Task, task_id)
    if task is None:
        raise ApiError("TASK_NOT_FOUND", "The requested task does not exist.", 404)
    project, role = accessible_project(task.project_id, user_id, WRITE_ROLES if write else None)
    task.project = project
    return task, role


def update_task(task: Task, data: TaskData, actor: User) -> Task:
    if "assigned_user_id" in data.provided_fields:
        _validate_assignee(task.project_id, data.assigned_user_id)
        task.assigned_user_id = data.assigned_user_id
    for field in ("title", "description", "status", "priority", "due_date"):
        if field in data.provided_fields:
            setattr(task, field, getattr(data, field))

    action = "TASK_COMPLETED" if data.status is TaskStatus.DONE else "TASK_UPDATED"
    db.session.add(
        ActivityLog(
            project_id=task.project_id,
            actor=actor,
            action=action,
            entity_type="task",
            entity_id=task.id,
            activity_metadata={"task_title": task.title},
        )
    )
    db.session.commit()
    return task


def delete_task(task: Task, actor: User) -> None:
    db.session.add(
        ActivityLog(
            project_id=task.project_id,
            actor=actor,
            action="TASK_DELETED",
            entity_type="task",
            entity_id=task.id,
            activity_metadata={"task_title": task.title},
        )
    )
    db.session.delete(task)
    db.session.commit()
