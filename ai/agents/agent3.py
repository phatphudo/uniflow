"""
Agent 3 — Interview Coach
Phase 1: MOCK_INTERVIEW_RESULT used for the skeleton demo.
Phase 5: call get_interview_coach().run(prompt) for real STAR evaluation.

System prompt is loaded from ai/prompts/agent3_interview_coach.md for easy versioning.
Agent is created lazily so Phase 1 works without API keys.
"""

from __future__ import annotations

from pathlib import Path
import wave
import sounddevice as sd
from ai.prompts import load_prompt
from config import settings
from schemas.agent3 import InterviewResult, StarScores
from openai import OpenAI
from pydantic_ai import Agent
import asyncio
import time
import threading

# Loaded from disk — edit ai/prompts/agent3_interview_coach.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent3_interview_coach")

_interview_coach = None


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

def _write_pcm16_wav(path: Path, frames, sample_rate: int, channels: int) -> None:
    """Persist int16 PCM frames to a WAV file."""
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # int16
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames.tobytes())


async def record_student_answer(
    filename: str,
    *,
    duration_seconds: float = 5.0, #Adjust longer for longer answers
    sample_rate: int = 16_000,
    channels: int = 1,
) -> Path:
    """Record a student's answer from the default input device and save as WAV."""
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be > 0")
    if channels <= 0:
        raise ValueError("channels must be > 0")

    output_path = Path(filename).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        recording = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
        )
        sd.wait()
    except Exception as exc:
        raise RuntimeError(f"Failed to record audio: {exc}") from exc

    _write_pcm16_wav(output_path, recording, sample_rate, channels)
    return output_path


def transcribe_student_answer(
    audio_path: str = "student_answer.wav",
    *,
    model: str | None = None,
) -> str:
    """Transcribe a WAV/MP3 file into text using OpenAI STT."""
    input_path = Path(audio_path).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Audio file not found: {input_path}")
    if input_path.stat().st_size == 0:
        raise ValueError(f"Audio file is empty: {input_path}")

    api_key = settings.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in .env.")

    client = OpenAI(api_key=api_key)
    with input_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model or settings.stt_model,
            file=audio_file,
        )

    text = (transcription.text or "").strip()
    if not text:
        raise RuntimeError("Transcription returned empty text.")
    return transcription.text

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

async def _demo() -> None:
    result = await get_interview_coach().run(MOCK_INTERVIEW_RESULT.model_dump_json())
    print(result.output)  # parsed InterviewResult

if __name__ == "__main__":
    print("Recorded student answer")
    asyncio.run(record_student_answer("student_answer.wav"))
    print("Recoding done")
    print(transcribe_student_answer("student_answer.wav"))