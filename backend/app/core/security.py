"""
Security & Auth Configuration
==============================
FastAPI-Users authentication strategy (JWT) and transport.
"""

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from app.core.config import settings

# ── Bearer Transport ────────────────────────────────────────────
bearer_transport = BearerTransport(tokenUrl="/api/auth/login")


# ── JWT Strategy ────────────────────────────────────────────────
def get_jwt_strategy() -> JWTStrategy:
    """Return JWT strategy using the secret from env."""
    return JWTStrategy(secret=settings.JWT_SECRET, lifetime_seconds=3600 * 24)  # 24h


# ── Authentication Backend ─────────────────────────────────────
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
