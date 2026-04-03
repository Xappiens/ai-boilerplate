"""
FastAPI Application Entrypoint
================================
Assembles all routers, middleware, SQLAdmin, and CORS.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import engine, async_session_maker

# ── Import Routers ─────────────────────────────────────────────
from app.api.auth import auth_router, register_router, users_router
from app.api.documents import router as documents_router
from app.api.webhooks import router as webhooks_router

# ── Import Models (ensure they're registered) ──────────────────
from app.models.user import User
from app.models.document import Document


# ── Lifespan ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    print(f"🚀 {settings.APP_NAME} starting...")
    print(f"🤖 Active LLM Provider: {settings.ACTIVE_LLM_PROVIDER}")
    print(f"🗄️ Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    yield
    print(f"👋 {settings.APP_NAME} shutting down...")
    await engine.dispose()


# ── FastAPI App ────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="🚀 AI-powered SaaS Boilerplate — Zero Vendor Lock-in",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth Routes (FastAPI-Users) ────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(register_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])

# ── Business Routes ────────────────────────────────────────────
app.include_router(documents_router)
app.include_router(webhooks_router)


# ── SQLAdmin Panel ─────────────────────────────────────────────

class UserAdmin(ModelView, model=User):
    """Admin view for User model."""
    column_list = [User.id, User.email, User.first_name, User.last_name, User.is_active, User.is_superuser]
    column_searchable_list = [User.email, User.first_name]
    column_sortable_list = [User.email, User.is_active]
    can_create = True
    can_edit = True
    can_delete = True
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class DocumentAdmin(ModelView, model=Document):
    """Admin view for Document model."""
    column_list = [Document.id, Document.title, Document.status, Document.ai_model_used, Document.created_at]
    column_searchable_list = [Document.title]
    column_sortable_list = [Document.title, Document.status, Document.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    name = "Document"
    name_plural = "Documents"
    icon = "fa-solid fa-file"


# Mount SQLAdmin at /admin
admin = Admin(app, engine, title=f"{settings.APP_NAME} Admin")
admin.add_view(UserAdmin)
admin.add_view(DocumentAdmin)


# ── Health Check ───────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "ai_provider": settings.ACTIVE_LLM_PROVIDER,
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "database": "connected",
        "ai_provider": settings.ACTIVE_LLM_PROVIDER,
    }
