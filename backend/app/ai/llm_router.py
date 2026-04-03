"""
AI Gateway - LLM Router
=========================
Universal AI routing through LiteLLM.
Zero vendor lock-in: swap models via environment variable.

Routing logic:
  - ollama/*   → Local container (http://ia_local:11434)
  - ovh/*      → OVH Sovereign Cloud (OpenAI-compatible endpoint)
  - gpt-*      → OpenAI
  - claude-*   → Anthropic
  - gemini-*   → Google
"""

import os
from typing import Optional

import litellm
from litellm import acompletion

from app.core.config import settings


# ── Configure LiteLLM ──────────────────────────────────────────
litellm.drop_params = True  # Ignore unsupported params per provider


async def generate_ai_response(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """
    Universal AI completion function.
    Routes to the correct provider based on ACTIVE_LLM_PROVIDER.

    Args:
        prompt: The user prompt to send.
        model: Override model name. Defaults to ACTIVE_LLM_PROVIDER.
        max_tokens: Maximum tokens in response.
        temperature: Creativity parameter.

    Returns:
        The AI-generated text response.
    """
    active_model = model or settings.ACTIVE_LLM_PROVIDER

    # Build kwargs based on provider
    kwargs: dict = {
        "model": active_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    # ── Provider-specific routing ──────────────────────────────
    if active_model.startswith("ollama/"):
        # Route to local Ollama container
        kwargs["api_base"] = settings.OLLAMA_API_BASE

    elif active_model.startswith("ovh/"):
        # Route to OVH sovereign cloud (OpenAI-compatible)
        # Map ovh/model to openai/model for LiteLLM compatibility
        kwargs["model"] = f"openai/{active_model.split('/', 1)[1]}"
        kwargs["api_base"] = settings.OVH_AI_BASE_URL
        kwargs["api_key"] = settings.OVH_AI_API_KEY

    else:
        # Standard commercial providers — LiteLLM handles routing
        # Ensure API keys are set in environment for LiteLLM
        if settings.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        if settings.ANTHROPIC_API_KEY:
            os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
        if settings.GEMINI_API_KEY:
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

    # ── Call LiteLLM ───────────────────────────────────────────
    response = await acompletion(**kwargs)
    return response.choices[0].message.content


async def generate_embedding(
    text: str,
    model: Optional[str] = None,
) -> list[float]:
    """
    Generate embeddings for text via LiteLLM.

    Args:
        text: Input text to embed.
        model: Embedding model. Defaults based on provider.

    Returns:
        List of floats representing the embedding vector.
    """
    active_model = model or settings.ACTIVE_LLM_PROVIDER

    # Determine embedding model based on provider
    if active_model.startswith("ollama/"):
        embed_model = "ollama/nomic-embed-text"
        response = await litellm.aembedding(
            model=embed_model,
            input=[text],
            api_base=settings.OLLAMA_API_BASE,
        )
    else:
        embed_model = "text-embedding-3-small"
        if settings.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        response = await litellm.aembedding(
            model=embed_model,
            input=[text],
        )

    return response.data[0]["embedding"]
