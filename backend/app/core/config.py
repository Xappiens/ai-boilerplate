"""
Application Configuration
=========================
Centralized settings using pydantic-settings.
All values are read from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Infrastructure ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://admin:secret_postgres_pass@db:5432/ia_database"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "super_secret_string_for_jwt_tokens"

    # ── AI Gateway ──────────────────────────────────────────────
    ACTIVE_LLM_PROVIDER: str = "ollama/llama3"
    OLLAMA_API_BASE: str = "http://ia_local:11434"

    # OVH Sovereign Cloud
    OVH_AI_API_KEY: str = ""
    OVH_AI_BASE_URL: str = ""

    # Commercial Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Async Agents
    MANUS_API_KEY: str = ""
    MANUS_API_URL: str = "https://api.manus.ai/v1/tasks"
    MANUS_WEBHOOK_SECRET: str = ""

    # ── App ─────────────────────────────────────────────────────
    APP_NAME: str = "AI Boilerplate"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
