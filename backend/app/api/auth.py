"""
Auth API Router
================
FastAPI-Users integration with JWT auth.
Exposes /api/auth/register and /api/auth/login.
"""

import logging
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.security import auth_backend
from app.models.user import User, UserCreate, UserRead, UserUpdate

logger = logging.getLogger(__name__)


# ── User Database Adapter ──────────────────────────────────────
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Provide SQLAlchemy user database adapter."""
    yield SQLAlchemyUserDatabase(session, User)


# ── User Manager ───────────────────────────────────────────────
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Custom user manager for business logic hooks."""

    reset_password_token_secret = settings.JWT_SECRET
    verification_token_secret = settings.JWT_SECRET

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        logger.info("✅ User %s registered (id=%s)", user.email, user.id)

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response=None,
    ) -> None:
        logger.info("🔑 User %s logged in", user.email)


async def get_user_manager(user_db=Depends(get_user_db)):
    """Dependency that provides the UserManager."""
    yield UserManager(user_db)


# ── FastAPI-Users Instance ─────────────────────────────────────
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Shortcut dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# ── Auth Routers ───────────────────────────────────────────────
auth_router = fastapi_users.get_auth_router(auth_backend)
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)
