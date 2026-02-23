"""
Agent 3 — Interview Coach
Phase 1: MOCK_INTERVIEW_RESULT used for the skeleton demo.
Phase 5: call get_interview_coach().run(prompt) for real STAR evaluation.

System prompt is loaded from ai/prompts/agent3_interview_coach.md for easy versioning.
Agent is created lazily so Phase 1 works without API keys.
"""

from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import io
import os
import subprocess
import tempfile
import wave
from ai.prompts import load_prompt
from config import settings
from schemas.agent3 import InterviewResult, StarScores
from openai import OpenAI
from pydantic_ai import Agent
from schemas.agent1 import PositionProfile
from ai.agents.agent1 import MOCK_POSITION_PROFILE
from schemas.agent3 import Agent3Input

# Loaded from disk — edit ai/prompts/agent3_interview_coach.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent3_interview_coach")

_interview_coach = None


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Return a cached OpenAI client — created once, reused on every call."""
    return OpenAI(api_key=settings.openai_api_key)


def get_interview_coach():
    """Return the PydanticAI Interview Coach agent, creating it on first call."""
    global _interview_coach
    if _interview_coach is None:

        _interview_coach = Agent(
            model=settings.ai_model,
            output_type=InterviewResult,
            system_prompt=_SYSTEM_PROMPT,
        )
    return _interview_coach



async def receive_student_answer(
    *,
    duration_seconds: float = 5.0,
    sample_rate: int = 16_000,
    channels: int = 1,
) -> str:
    """Record from microphone and transcribe directly — no file saved."""
    import sounddevice as sd

    recording = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
    )
    sd.wait()

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # int16
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(recording.tobytes())
    buffer.seek(0)
    buffer.name = "answer.wav"  # OpenAI SDK needs a .name to detect format

    transcription = get_openai_client().audio.transcriptions.create(
        model=settings.stt_model,
        file=buffer,
    )
    return (transcription.text or "").strip()

# In agent3.py — new version of text_to_speech
def get_question_audio(question: str, model: str | None = None) -> bytes:
    """Return TTS audio bytes — play with st.audio() in Streamlit."""
    response = get_openai_client().audio.speech.create(
        model=model or settings.agent3_model,
        voice="alloy",
        input=question.strip(),
    )
    return response.read()  # raw MP3 bytes

# ── Mock pipeline helpers ─────────────────────────────────────────────────────
MOCK_STUDENT_ANSWER = (
    "During my internship, our team had conflicting requests from design and sales "
    "for the roadmap. I was responsible for prioritization. I built a scorecard with "
    "impact and effort, aligned stakeholders in a working session, and proposed a plan. "
    "We shipped the top 3 features and improved weekly active users by 11%."
)


def _mock_star_score(student_answer: str) -> StarScores:
    """Rule-based STAR scoring for local mock runs (no model call)."""
    text = student_answer.lower()

    # Situation: context cues
    situation = 10
    if any(k in text for k in ("during", "at my", "team", "project", "internship")):
        situation += 8
    if len(student_answer) > 200:
        situation += 3

    # Task: ownership cues
    task = 8
    if any(k in text for k in ("i was responsible", "my role", "owned", "responsible")):
        task += 10

    # Action: concrete verbs
    action = 8
    action_hits = sum(
        1
        for k in ("built", "analyzed", "aligned", "proposed", "implemented", "led")
        if k in text
    )
    action += min(action_hits * 3, 12)

    # Result: measurable outcomes
    result = 6
    if any(k in text for k in ("%","increased","reduced","improved","grew","saved")):
        result += 14
    if any(k in text for k in ("users", "revenue", "retention", "nps", "conversion")):
        result += 4

    # Clamp to schema range
    return StarScores(
        situation=max(0, min(25, situation)),
        task=max(0, min(25, task)),
        action=max(0, min(25, action)),
        result=max(0, min(25, result)),
    )


def run_mock_agent3_pipeline(student_answer: str | None = None) -> InterviewResult:
    """
    Local mock of Agent 3 pipeline:
    1) use mock student profile/context
    2) get (mock) student answer
    3) return STAR-style judged InterviewResult
    """
    _ = MOCK_AGENT3_INPUT.position_profile  # mock profile/context source
    question = MOCK_GENERATED_QUESTION.question
    answer = student_answer or MOCK_STUDENT_ANSWER
    score = _mock_star_score(answer)

    strengths: list[str] = []
    improvements: list[str] = []

    if score.situation >= 16:
        strengths.append("Context is clear and grounded in a real scenario.")
    else:
        improvements.append("Make the Situation more specific (team, timeline, constraints).")

    if score.task >= 16:
        strengths.append("Your personal ownership and responsibility are explicit.")
    else:
        improvements.append("Clarify your exact task and scope of ownership.")

    if score.action >= 16:
        strengths.append("Actions are concrete and show decision-making.")
    else:
        improvements.append("Describe your actions step-by-step with concrete methods.")

    if score.result >= 16:
        strengths.append("Result includes measurable impact.")
    else:
        improvements.append("Add measurable outcomes (%, KPI change, business impact).")

    return InterviewResult(
        question=question,
        student_answer=answer,
        star_scores=score,
        strengths=strengths or ["Solid baseline answer structure."],
        improvements=improvements,
        stronger_closing=(
            "A stronger close: 'The prioritized roadmap shipped in 6 weeks and "
            "improved weekly active users by 11%, and I reused the framework for the "
            "next planning cycle.'"
        ),
    )







# ── Phase 1 mock ──────────────────────────────────────────────────────────────
MOCK_INTERVIEW_RESULT = InterviewResult(
    question=(
        "Describe a time you took ownership of defining the roadmap for a product area — "
        "how did you decide what to build, align stakeholders with competing priorities, "
        "and measure success after launch?"
    ),
    student_answer=(
        "In my internship I helped the team decide which features to ship for Q3. "
        "I talked to a few users and wrote up my recommendations. The team liked them "
        "and we shipped on time."
    ),
    star_scores=StarScores(situation=14, task=10, action=12, result=8),
    strengths=[
        "Demonstrated initiative in collecting user feedback.",
        "Clear outcome mentioned — shipped on time.",
    ],
    improvements=[
        "Situation lacked specificity — what was the product, team size, constraints?",
        "Task was vague — what exactly was your role vs the team's?",
        "Actions need more concrete detail — which frameworks or methods did you use?",
        "Result had no measurable impact — revenue, retention, NPS?",
    ],
    stronger_closing=(
        "A stronger close: 'The feature shipped in Q3 and drove a 12% increase in DAU "
        "within 30 days. I presented the results to the VP, which led to the team "
        "doubling down on the initiative in Q4.'"
    ),
)
#--------------Second Mock ---------------------
MOCK_GENERATED_QUESTION = InterviewResult(
    question=(
        "Tell me about a time you had to align engineering, design, and business "
        "stakeholders around a product roadmap decision with conflicting priorities."
    ),
    student_answer="",
    star_scores=StarScores(situation=0, task=0, action=0, result=0),
    strengths=[],
    improvements=[],
    stronger_closing="",
)

MOCK_AGENT3_INPUT = Agent3Input(
    position_profile=MOCK_POSITION_PROFILE,
    previous_interview_results=[MOCK_INTERVIEW_RESULT],
    previous_interview_result=MOCK_INTERVIEW_RESULT,
    student_answer="",
)

async def _demo() -> None:
    result = await get_interview_coach().run(MOCK_INTERVIEW_RESULT.model_dump_json())
    print(result.output)  # parsed InterviewResult

if __name__ == "__main__":
    # print("Recorded student answer")
    # asyncio.run(record_student_answer("student_answer.wav"))
    # print("Recoding done")
    # print(transcribe_student_answer("student_answer.wav"))
    # #Record the answer -> Transcript it -> pass it to AI -> AI judging
    print("demo mock pipeline")
    print(run_mock_agent3_pipeline().model_dump_json(indent=2))
    get_question_audio("Tell me about a time you handled competing priorities.")
