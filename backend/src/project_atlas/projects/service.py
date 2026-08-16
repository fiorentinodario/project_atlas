from uuid import UUID

from sqlalchemy import select

from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import ActivityLog, Project, ProjectMember, User
from project_atlas.models.enums import ProjectRole
from project_atlas.projects.schemas import ProjectCreateData, ProjectUpdateData


def serialize_project(project: Project, role: ProjectRole) -> dict:
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "role": role.value,
        "owner": {
            "id": str(project.owner.id),
            "display_name": project.owner.display_name,
        },
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def accessible_project(
    project_id: UUID,
    user_id: UUID,
    allowed_roles: set[ProjectRole] | None = None,
) -> tuple[Project, ProjectRole]:
    result = db.session.execute(
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == user_id)
    ).one_or_none()
    if result is None:
        raise ApiError("PROJECT_NOT_FOUND", "The requested project does not exist.", 404)

    project, role = result
    if allowed_roles is not None and role not in allowed_roles:
        raise ApiError("PROJECT_ACCESS_DENIED", "You cannot perform this project action.", 403)
    return project, role


def list_projects(user_id: UUID, page: int, per_page: int):
    statement = (
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id)
        .order_by(Project.updated_at.desc())
    )
    return db.paginate(statement, page=page, per_page=per_page, error_out=False)


def create_project(data: ProjectCreateData, owner: User) -> Project:
    project = Project(name=data.name, description=data.description, owner=owner)
    db.session.add(project)
    db.session.flush()
    db.session.add_all(
        [
            ProjectMember(project=project, user=owner, role=ProjectRole.OWNER),
            ActivityLog(
                project=project,
                actor=owner,
                action="PROJECT_CREATED",
                entity_type="project",
                entity_id=project.id,
                activity_metadata={"project_name": project.name},
            ),
        ]
    )
    db.session.commit()
    return project


def update_project(project: Project, data: ProjectUpdateData, actor: User) -> Project:
    if data.name is not None:
        project.name = data.name
    if data.description_provided:
        project.description = data.description
    if data.status is not None:
        project.status = data.status
    db.session.add(
        ActivityLog(
            project=project,
            actor=actor,
            action="PROJECT_UPDATED",
            entity_type="project",
            entity_id=project.id,
        )
    )
    db.session.commit()
    return project


def delete_project(project: Project) -> None:
    db.session.delete(project)
    db.session.commit()
