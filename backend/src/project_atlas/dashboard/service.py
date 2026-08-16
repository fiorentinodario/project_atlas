from uuid import UUID

from sqlalchemy import func, select

from project_atlas.extensions import db
from project_atlas.models import ActivityLog, Document, Project, ProjectMember, Task
from project_atlas.models.enums import ProjectStatus, TaskStatus


def dashboard_data(user_id: UUID) -> dict:
    project_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
    projects = list(
        db.session.scalars(
            select(Project)
            .where(Project.id.in_(project_ids))
            .order_by(Project.updated_at.desc())
            .limit(6)
        )
    )
    task_counts = dict(
        db.session.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.project_id.in_(project_ids))
            .group_by(Task.status)
        )
        .tuples()
        .all()
    )
    active_projects = (
        db.session.scalar(
            select(func.count(Project.id)).where(
                Project.id.in_(project_ids), Project.status == ProjectStatus.ACTIVE
            )
        )
        or 0
    )
    recent_projects = []
    for project in projects:
        counts = dict(
            db.session.execute(
                select(Task.status, func.count(Task.id))
                .where(Task.project_id == project.id)
                .group_by(Task.status)
            )
            .tuples()
            .all()
        )
        total = sum(counts.values())
        done = counts.get(TaskStatus.DONE, 0)
        document_count = (
            db.session.scalar(
                select(func.count(Document.id)).where(Document.project_id == project.id)
            )
            or 0
        )
        recent_projects.append(
            {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status.value,
                "task_count": total,
                "document_count": document_count,
                "progress": round(done / total * 100) if total else 0,
                "updated_at": project.updated_at.isoformat(),
            }
        )
    activities = db.session.execute(
        select(ActivityLog, Project)
        .join(Project, Project.id == ActivityLog.project_id)
        .where(ActivityLog.project_id.in_(project_ids))
        .order_by(ActivityLog.created_at.desc())
        .limit(12)
    )
    return {
        "stats": {
            "active_projects": active_projects,
            "total_tasks": sum(task_counts.values()),
            "tasks_in_progress": task_counts.get(TaskStatus.IN_PROGRESS, 0),
            "completed_tasks": task_counts.get(TaskStatus.DONE, 0),
        },
        "recent_projects": recent_projects,
        "recent_activity": [
            {
                "id": str(activity.id),
                "action": activity.action,
                "metadata": activity.activity_metadata,
                "created_at": activity.created_at.isoformat(),
                "project": {"id": str(project.id), "name": project.name},
                "actor": (
                    {
                        "id": str(activity.actor.id),
                        "display_name": activity.actor.display_name,
                    }
                    if activity.actor
                    else None
                ),
            }
            for activity, project in activities
        ],
    }
