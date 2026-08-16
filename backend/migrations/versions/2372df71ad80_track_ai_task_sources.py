"""track ai task sources

Revision ID: 2372df71ad80
Revises: 6c8c5c8376d1
Create Date: 2026-08-16 22:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2372df71ad80"
down_revision = "6c8c5c8376d1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source_analysis_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("source_suggestion_index", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tasks_source_analysis_id_ai_analyses",
            "ai_analyses",
            ["source_analysis_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_unique_constraint(
            "uq_task_analysis_suggestion",
            ["source_analysis_id", "source_suggestion_index"],
        )
        batch_op.create_index(
            batch_op.f("ix_tasks_source_analysis_id"), ["source_analysis_id"], unique=False
        )


def downgrade():
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tasks_source_analysis_id"))
        batch_op.drop_constraint("uq_task_analysis_suggestion", type_="unique")
        batch_op.drop_constraint("fk_tasks_source_analysis_id_ai_analyses", type_="foreignkey")
        batch_op.drop_column("source_suggestion_index")
        batch_op.drop_column("source_analysis_id")
