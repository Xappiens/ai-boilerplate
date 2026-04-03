"""
ARQ Worker
==========
Background task processor using ARQ (async Redis queue).
Handles heavy AI operations without blocking the API server.
"""

import uuid
from datetime import datetime, timezone

from arq import create_pool
from arq.connections import RedisSettings

from app.ai.llm_router import generate_ai_response, generate_embedding
from app.core.config import settings
from app.core.database import async_session_maker
from app.models.document import Document, DocumentStatus


def parse_redis_url(url: str) -> RedisSettings:
    """Parse a redis:// URL into ARQ RedisSettings."""
    # redis://redis:6379/0
    url = url.replace("redis://", "")
    parts = url.split("/")
    host_port = parts[0]
    database = int(parts[1]) if len(parts) > 1 else 0
    host, port = host_port.split(":")
    return RedisSettings(host=host, port=int(port), database=database)


# ── Task Functions ─────────────────────────────────────────────

async def process_document_ia(ctx: dict, doc_id: str) -> dict:
    """
    Heavy AI processing task — runs in background worker.

    1. Reads the document from DB
    2. Calls LLM for summary generation
    3. Generates embedding vector
    4. Saves results back to DB

    Args:
        ctx: ARQ context (contains Redis pool).
        doc_id: UUID of the document to process.

    Returns:
        dict with processing status and model used.
    """
    print(f"🤖 [Worker] Processing document {doc_id}...")

    async with async_session_maker() as session:
        # 1. Load document
        doc = await session.get(Document, uuid.UUID(doc_id))
        if not doc:
            print(f"❌ [Worker] Document {doc_id} not found")
            return {"status": "error", "message": "Document not found"}

        # 2. Update status to processing
        doc.status = DocumentStatus.PROCESSING
        doc.ai_model_used = settings.ACTIVE_LLM_PROVIDER
        session.add(doc)
        await session.commit()

        try:
            # 3. Generate AI summary
            prompt = (
                f"Genera un resumen conciso del siguiente documento:\n\n"
                f"Título: {doc.title}\n"
                f"Contenido: {doc.content[:4000]}\n\n"
                f"Resumen:"
            )
            summary = await generate_ai_response(prompt, max_tokens=512)
            doc.ai_summary = summary

            # 4. Generate embedding vector
            try:
                embedding = await generate_embedding(doc.content[:8000])
                doc.embedding = embedding
            except Exception as embed_err:
                print(f"⚠️ [Worker] Embedding generation skipped: {embed_err}")

            # 5. Mark as completed
            doc.status = DocumentStatus.COMPLETED
            doc.updated_at = datetime.now(timezone.utc)
            session.add(doc)
            await session.commit()

            print(f"✅ [Worker] Document {doc_id} processed successfully")
            return {
                "status": "completed",
                "model": settings.ACTIVE_LLM_PROVIDER,
                "summary_length": len(summary),
            }

        except Exception as e:
            # Mark as failed
            doc.status = DocumentStatus.FAILED
            doc.updated_at = datetime.now(timezone.utc)
            session.add(doc)
            await session.commit()

            print(f"❌ [Worker] Document {doc_id} failed: {e}")
            return {"status": "failed", "error": str(e)}


# ── ARQ Worker Configuration ──────────────────────────────────

class WorkerSettings:
    """ARQ Worker settings — connects to Redis and registers task functions."""

    redis_settings = parse_redis_url(settings.REDIS_URL)
    functions = [process_document_ia]
    max_jobs = 10
    job_timeout = 600  # 10 minutes max per job
