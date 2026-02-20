"""
config.py — Application settings loaded from environment variables.

Usage anywhere in the project:
    from config import settings

    model = settings.ai_model
    key   = settings.serper_api_key
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # silently ignore unrecognised env vars
    )

    # ── LLM ────────────────────────────────────────────────────────────────────
    ai_model: str = "google-gla:gemini-1.5-pro"
    """PydanticAI model string. Examples:
       'google-gla:gemini-1.5-pro'   (Google Gemini via Generative Language API)
       'openai:gpt-4o'               (OpenAI)
    """

    # ── API Keys ────────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    """Required when ai_model starts with 'openai:'."""

    serper_api_key: str = ""
    """Required for live event search in Agent 2 (Phase 4+)."""


# Singleton — import this everywhere instead of instantiating Settings() yourself.
settings = Settings()
