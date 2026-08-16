from sqlalchemy import inspect

from project_atlas.extensions import db
from project_atlas.models import Project, ProjectMember, Task, User
from project_atlas.models.enums import (
    ProjectRole,
    ProjectStatus,
    TaskPriority,
    TaskSource,
    TaskStatus,
)


def test_initial_schema_contains_expected_tables(app) -> None:
    with app.app_context():
        assert set(inspect(db.engine).get_table_names()) == {
            "activity_logs",
            "ai_analyses",
            "document_chunks",
            "documents",
            "project_decisions",
            "project_members",
            "projects",
            "refresh_tokens",
            "tasks",
            "users",
        }


def test_project_membership_and_task_defaults_are_persisted(app) -> None:
    with app.app_context():
        user = User(
            email="owner@example.com",
            password_hash="not-a-real-password-hash",
            display_name="Project Owner",
        )
        project = Project(name="Atlas", owner=user)
        membership = ProjectMember(project=project, user=user, role=ProjectRole.OWNER)
        task = Task(title="Define schema", project=project, created_by=user)
        db.session.add_all([membership, task])
        db.session.commit()

        assert project.status is ProjectStatus.ACTIVE
        assert task.status is TaskStatus.TODO
        assert task.priority is TaskPriority.MEDIUM
        assert task.source is TaskSource.MANUAL
        assert project.members[0].user.email == "owner@example.com"
