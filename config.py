"""
config.py — Application settings loaded from environment variables.

Usage anywhere in the project:
    from config import settings

    model = settings.ai_model
    key   = settings.serper_api_key
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # silently ignore unrecognised env vars
    )

    # ── LLM ────────────────────────────────────────────────────────────────────
    ai_model: str = os.getenv("AI_MODEL")
    """PydanticAI model string. Examples:
       'google-gla:gemini-1.5-pro'   (Google Gemini via Generative Language API)
       'openai:gpt-4o'               (OpenAI)
    """
    # -- TTS and STT Agents ────────────────────────────────────────────────────
    agent3_model: str = "openai:gpt-4o-tts"
    stt_model: str = "gpt-4o-mini-transcribe"

    # ── API Keys ────────────────────────────────────────────────────────────────
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    """Required when ai_model starts with 'openai:'."""

    serper_api_key: str = os.getenv("SERPER_API_KEY")
    """Required for live event search in Agent 2 (Phase 4+)."""


# Singleton — import this everywhere instead of instantiating Settings() yourself.
settings = Settings()
