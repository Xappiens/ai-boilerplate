"""
Documents API Router
=====================
CRUD endpoints for documents + async AI processing trigger.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from arq import create_pool
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.auth import current_active_user
from app.core.config import settings
from app.core.database import get_async_session
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.worker import parse_redis_url

router = APIRouter(prefix="/api/documents", tags=["Documents"])


# ── Request / Response Schemas ─────────────────────────────────

class DocumentCreate(BaseModel):
    title: str
    content: str = ""


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    status: str
    ai_summary: Optional[str] = None
    ai_model_used: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskEnqueuedResponse(BaseModel):
    message: str
    document_id: uuid.UUID
    status: str = "queued"


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """List all documents owned by the current user."""
    query = select(Document).where(Document.owner_id == user.id)
    result = await session.execute(query)
    documents = result.scalars().all()
    return documents


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Create a new document."""
    doc = Document(
        title=data.title,
        content=data.content,
        owner_id=user.id,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get a specific document."""
    doc = await session.get(Document, doc_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Delete a document."""
    doc = await session.get(Document, doc_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    await session.delete(doc)
    await session.commit()


@router.post(
    "/{doc_id}/process",
    response_model=TaskEnqueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_document(
    doc_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Enqueue a document for AI processing.

    This endpoint does NOT call the AI directly.
    It enqueues the task in Redis (ARQ) and returns HTTP 202 immediately.
    The ARQ worker picks up the job and processes it in the background.
    """
    # Verify document exists and belongs to user
    doc = await session.get(Document, doc_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == DocumentStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Document is already being processed")

    # Update status to queued
    doc.status = DocumentStatus.QUEUED
    doc.updated_at = datetime.now(timezone.utc)
    session.add(doc)
    await session.commit()

    # Enqueue task in Redis via ARQ
    redis_pool = await create_pool(parse_redis_url(settings.REDIS_URL))
    await redis_pool.enqueue_job("process_document_ia", str(doc_id))
    await redis_pool.close()

    return TaskEnqueuedResponse(
        message="Tarea encolada. Procesando en segundo plano...",
        document_id=doc_id,
    )
