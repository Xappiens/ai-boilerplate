"""Initial migration - create tables and pgvector extension

Revision ID: 001_initial
Revises:
Create Date: 2026-04-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── CRITICAL: Enable pgvector extension BEFORE creating tables ──
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ── Users table (FastAPI-Users) ──
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ── Documents table (with pgvector) ──
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_model_used", sa.String(length=100), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_id"), "documents", ["id"])
    op.create_index(op.f("ix_documents_title"), "documents", ["title"])
    op.create_index(op.f("ix_documents_owner_id"), "documents", ["owner_id"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector;")
