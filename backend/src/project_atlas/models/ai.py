from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project_atlas.extensions import db
from project_atlas.models.base import TimestampMixin


class AIAnalysis(TimestampMixin, db.Model):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    open_questions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    risks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    suggested_tasks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)

    project: Mapped[Project] = relationship(back_populates="analyses")
    requested_by: Mapped[User] = relationship()


from project_atlas.models.core import Project, User  # noqa: E402
