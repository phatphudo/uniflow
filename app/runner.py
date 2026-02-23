"""
app/runner.py — Orchestrator invocation.

build_stub_deps() constructs Phase-1 placeholder dependencies.
run_analysis()   calls run_uniflow() and returns a FinalReport.

Phase 6: swap build_stub_deps() for real ChromaDB + Calendar deps.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from ai.agents.deps import OrchestratorDeps
from ai.orchestrator import run_uniflow
from app.sidebar import UserInputs
from schemas.inputs import TranscriptData
from schemas.report import FinalReport
from config import settings

# A dedicated thread pool so async coroutines run in a fresh event loop,
# avoiding conflicts with Streamlit's uvloop.
_pool = ThreadPoolExecutor(max_workers=2)


def run_async(coro):
    """Run an async coroutine in a fresh event loop on a background thread."""
    return _pool.submit(asyncio.run, coro).result()


def build_stub_deps() -> OrchestratorDeps:
    """
    Phase 1 stub dependencies — no real calendar service wired.
    Replace with real Calendar API client in Phase 6.
    """
    return OrchestratorDeps(
        resume_text="",
        transcript_data=TranscriptData(student_name="", gpa=0.0, completed=[]),
        calendar_service=None,
        search_api_key=settings.serper_api_key,
    )


def run_analysis(inputs: UserInputs) -> FinalReport:
    """Invoke the orchestrator with a spinner and return the FinalReport."""
    deps = build_stub_deps()

    with st.spinner("Analyzing your profile..."):
        report = run_async(
            run_uniflow(
                resume_pdf_path=inputs.resume_file if inputs.resume_file else "mock.pdf",
                transcript_pdf_path=inputs.transcript_file if inputs.transcript_file else "mock.pdf",
                target_position=inputs.target_position,
                deps=deps,
                use_mocks=False,
            )
        )
    return report
