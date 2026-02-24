"""
app/runner.py — Shared async helpers and dependency builder.

run_async()       — runs an async coroutine on a background thread (Streamlit-safe).
build_stub_deps() — builds OrchestratorDeps until real ChromaDB + Calendar are wired.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

from ai.agents.deps import OrchestratorDeps
from ai.orchestrator import run_uniflow
from app.sidebar import UserInputs
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


def run_analysis(inputs: UserInputs):
    """Save uploaded PDFs to temp files and run the full UniFlow pipeline."""
    resume_path = transcript_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(inputs.resume_file.read())
            resume_path = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(inputs.transcript_file.read())
            transcript_path = f.name

        deps = build_stub_deps()
        return run_async(
            run_uniflow(
                resume_pdf_path=resume_path,
                transcript_pdf_path=transcript_path,
                target_position=inputs.target_position,
                program_enrolled=inputs.program_enrolled,
                credits_remaining=inputs.credits_remaining,
                deps=deps,
            )
        )
    finally:
        if resume_path and os.path.exists(resume_path):
            os.unlink(resume_path)
        if transcript_path and os.path.exists(transcript_path):
            os.unlink(transcript_path)
