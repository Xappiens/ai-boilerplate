"""
AI Gateway - Manus Async Agent Client
=======================================
Dispatches complex tasks to external AI agents via HTTP.
Fire-and-forget pattern: sends the task and returns immediately.
The agent calls back via webhook when done.
"""

import httpx

from app.core.config import settings


async def dispatch_to_manus(
    task_description: str,
    document_id: str,
    callback_url: str = "/api/webhooks/manus",
) -> dict:
    """
    Send a task to the Manus AI agent asynchronously.

    The agent will process the task (potentially for minutes/hours)
    and call back via the webhook endpoint when finished.

    Args:
        task_description: Natural language description of the task.
        document_id: ID of the document being processed.
        callback_url: Webhook URL for the agent to call back.

    Returns:
        dict with task_id and status from the agent API.
    """
    payload = {
        "task": task_description,
        "metadata": {
            "document_id": document_id,
            "callback_url": callback_url,
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.MANUS_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.MANUS_API_URL,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
