"""
Webhooks API Router
====================
Receives async callbacks from external AI agents (e.g., Manus).
"""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


# ── Schemas ────────────────────────────────────────────────────

class ManusWebhookPayload(BaseModel):
    task_id: str
    status: str  # "completed" | "failed"
    document_id: str
    result: Optional[str] = None
    error: Optional[str] = None


# ── Signature Verification ─────────────────────────────────────

def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    if not secret:
        return True  # Skip verification if no secret configured
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


# ── Endpoint ───────────────────────────────────────────────────

@router.post("/manus", status_code=status.HTTP_200_OK)
async def manus_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(default=None),
):
    """
    Receive results from the Manus AI agent.

    This endpoint is called asynchronously by the agent when it finishes
    processing a task (could be minutes or hours after dispatch).

    Flow:
    1. Validate webhook signature
    2. Parse payload
    3. Update document in PostgreSQL
    4. Mark as completed/failed
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    if settings.MANUS_WEBHOOK_SECRET and x_webhook_signature:
        if not verify_webhook_signature(
            body, x_webhook_signature, settings.MANUS_WEBHOOK_SECRET
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature",
            )

    # Parse payload
    payload = ManusWebhookPayload.model_validate_json(body)

    # Update document in database
    async with async_session_maker() as session:
        doc = await session.get(Document, uuid.UUID(payload.document_id))
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {payload.document_id} not found",
            )

        if payload.status == "completed" and payload.result:
            doc.status = DocumentStatus.COMPLETED
            doc.ai_summary = payload.result
            doc.ai_model_used = "manus-agent"
        else:
            doc.status = DocumentStatus.FAILED

        doc.updated_at = datetime.now(timezone.utc)
        session.add(doc)
        await session.commit()

    logger.info("📨 [Webhook] Manus result for doc %s: %s", payload.document_id, payload.status)
    return {"received": True, "document_id": payload.document_id}
