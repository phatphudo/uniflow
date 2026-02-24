"""
app/runner.py — Shared async helpers and dependency builder.

run_async()       — runs an async coroutine on a background thread (Streamlit-safe).
build_stub_deps() — builds OrchestratorDeps until real ChromaDB + Calendar are wired.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from ai.agents.deps import OrchestratorDeps
from config import settings
from schemas.inputs import TranscriptData

# Dedicated thread pool — avoids conflicts with Streamlit's own event loop.
_pool = ThreadPoolExecutor(max_workers=2)


def run_async(coro):
    """Run an async coroutine in a fresh event loop on a background thread."""
    return _pool.submit(asyncio.run, coro).result()


def build_stub_deps() -> OrchestratorDeps:
    """
    Stub dependencies — no real ChromaDB or Calendar service wired yet.
    Phase 6: replace with real clients.
    """
    return OrchestratorDeps(
        resume_text="",
        transcript_data=TranscriptData(student_name="", gpa=0.0, completed=[]),
        calendar_service=None,
        search_api_key=settings.serper_api_key,
    )
