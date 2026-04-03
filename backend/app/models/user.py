"""
User Model
==========
SQLModel User table integrated with FastAPI-Users.
"""

import uuid
from typing import Optional

from fastapi_users import schemas
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlmodel import Field, SQLModel


# ── Database Table ──────────────────────────────────────────────
class User(SQLAlchemyBaseUserTableUUID, SQLModel, table=True):
    """User table stored in PostgreSQL. Managed by FastAPI-Users."""

    __tablename__ = "users"

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)


# ── Pydantic Schemas for FastAPI-Users ──────────────────────────
class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema returned when reading a user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating a user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
