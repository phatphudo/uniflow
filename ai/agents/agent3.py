"""
Agent 3 — Interview Coach
Phase 1: MOCK_INTERVIEW_RESULT used for the skeleton demo.
Phase 5: call get_interview_coach().run(prompt) for real STAR evaluation.

System prompt is loaded from ai/prompts/agent3_interview_coach.md for easy versioning.
Agent is created lazily so Phase 1 works without API keys.
"""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI
from pydantic_ai import Agent

from ai.prompts import load_prompt
from config import settings
from schemas.agent3 import InterviewResult

# Loaded from disk — edit ai/prompts/agent3_interview_coach.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent3_interview_coach")


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Return a cached OpenAI client — created once, reused on every call."""
    return OpenAI(api_key=settings.openai_api_key)


@lru_cache(maxsize=1)
def get_interview_coach() -> Agent:
    """Return the PydanticAI Interview Coach agent, creating it on first call."""
    return Agent(
        model=settings.ai_model,
        output_type=InterviewResult,
        system_prompt=_SYSTEM_PROMPT,
    )


def get_question_audio(question: str, voice: str = "alloy") -> bytes:
    """Return MP3 bytes for TTS rendering of question (for use with st.audio())."""
    response = get_openai_client().audio.speech.create(
        model=settings.agent3_model,
        voice=voice,
        input=question.strip(),
    )
    if hasattr(response, "read"):
        return response.read()
    return b"".join(response.iter_bytes())


async def generate_question(
    top_gap: str,
    interview_topics: list[str],
    target_position: str,
    previous_results: list[InterviewResult],
) -> str:
    """Generate the next interview question and return it as a string."""
    history_json = [r.model_dump() for r in previous_results]
    prompt = (
        f"mode: generate_question\n"
        f"top_gap: {top_gap}\n"
        f"interview_topics: {interview_topics}\n"
        f"position_context: {target_position}\n"
        f"previous_interview_results: {history_json}\n"
        f"student_answer: \n"
    )
    result = await get_interview_coach().run(prompt)
    return result.output.question


async def evaluate_answer(
    question: str,
    student_answer: str,
    top_gap: str,
    interview_topics: list[str],
    target_position: str,
    previous_results: list[InterviewResult],
) -> InterviewResult:
    """Evaluate a student's STAR answer and return a full InterviewResult."""
    history_json = [r.model_dump() for r in previous_results]
    prompt = (
        f"mode: evaluate_answer\n"
        f"question: {question}\n"
        f"top_gap: {top_gap}\n"
        f"interview_topics: {interview_topics}\n"
        f"position_context: {target_position}\n"
        f"previous_interview_results: {history_json}\n"
        f"student_answer: {student_answer}\n"
    )
    result = await get_interview_coach().run(prompt)
    return result.output
