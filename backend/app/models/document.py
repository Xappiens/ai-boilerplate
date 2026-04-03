"""
Document Model
==============
SQLModel table with pgvector embedding support.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, text
from sqlmodel import Field, SQLModel


class DocumentStatus(str, Enum):
    """Processing status for documents."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(SQLModel, table=True):
    """
    Document table with vector embeddings for RAG.
    The `embedding` field stores dense vectors via pgvector extension.
    """

    __tablename__ = "documents"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    title: str = Field(max_length=500, index=True)
    content: str = Field(default="")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    ai_summary: Optional[str] = Field(default=None)
    ai_model_used: Optional[str] = Field(default=None)

    # pgvector embedding (1536 dims — compatible with OpenAI ada-002 / adjustable)
    embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(Vector(1536), nullable=True),
    )

    # Metadata
    owner_id: Optional[uuid.UUID] = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": text("now()")},
    )
    updated_at: Optional[datetime] = Field(default=None)
