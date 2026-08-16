from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project_atlas.extensions import db
from project_atlas.models.base import TimestampMixin
from project_atlas.models.enums import ProjectRole, ProjectStatus


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    owned_projects: Mapped[list[Project]] = relationship(back_populates="owner")
    memberships: Mapped[list[ProjectMember]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Project(TimestampMixin, db.Model):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    owner: Mapped[User] = relationship(back_populates="owned_projects")
    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list[Task]] = relationship(back_populates="project", cascade="all, delete-orphan")
    decisions: Mapped[list[ProjectDecision]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[list[AIAnalysis]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list[ActivityLog]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectMember(TimestampMixin, db.Model):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role"),
        default=ProjectRole.MEMBER,
        nullable=False,
    )

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


from project_atlas.models.ai import AIAnalysis  # noqa: E402
from project_atlas.models.work import ActivityLog, Document, ProjectDecision, Task  # noqa: E402
