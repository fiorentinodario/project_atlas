"""add document embeddings

Revision ID: 6c8c5c8376d1
Revises: 842a80e7de94
Create Date: 2026-08-16 20:20:00.000000

"""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "6c8c5c8376d1"
down_revision = "842a80e7de94"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("indexing_error", sa.Text(), nullable=True))

    with op.batch_alter_table("document_chunks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("embedding", Vector(1536), nullable=True))


def downgrade():
    with op.batch_alter_table("document_chunks", schema=None) as batch_op:
        batch_op.drop_column("embedding")

    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_column("indexing_error")
        batch_op.drop_column("indexed_at")
