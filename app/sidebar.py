"""
app/sidebar.py — Sidebar inputs.

render_sidebar() draws the sidebar and returns a UserInputs dataclass
containing everything the rest of the app needs from the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st


@dataclass
class UserInputs:
    target_position: str
    resume_file: Any  # UploadedFile | None
    transcript_file: Any  # UploadedFile | None
    student_answer: str
    run_clicked: bool


_DEFAULT_ANSWER = (
    "In my internship I helped the team decide which features to ship for Q3. "
    "I talked to a few users and wrote up my recommendations. The team liked them "
    "and we shipped on time."
)


def _transcribe(audio_file) -> str:
    """Transcribe an uploaded audio file using OpenAI Whisper. Returns empty string on failure."""
    try:
        from ai.agents.agent3 import get_openai_client
        from config import settings
        transcription = get_openai_client().audio.transcriptions.create(
            model=settings.stt_model,
            file=audio_file,
        )
        return (transcription.text or "").strip()
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return ""


def render_sidebar() -> UserInputs:
    """Render the sidebar UI and return the collected user inputs."""
    with st.sidebar:
        st.markdown("## 🎓 UniFlow AI")
        st.markdown("*Career Readiness Engine*")
        st.divider()

        target_position = st.text_input(
            "🎯 Target Position",
            placeholder="e.g. Product Manager at a tech startup",
            value="Product Manager at a tech startup",
        )

        resume_file = st.file_uploader("📄 Resume (PDF)", type=["pdf"])
        transcript_file = st.file_uploader("📋 Transcript (PDF)", type=["pdf"])

        st.divider()
        st.markdown("#### 🎤 Mock Interview")

        # ── Voice answer upload (optional) ────────────────────────────────────
        audio_file = st.file_uploader(
            "🎙️ Upload voice answer (MP3 / WAV / M4A)",
            type=["mp3", "wav", "m4a"],
        )

        if audio_file is not None:
            # Cache transcription so we don't re-call Whisper on every rerun
            cache_key = f"stt_{audio_file.name}_{audio_file.size}"
            if cache_key not in st.session_state:
                with st.spinner("Transcribing voice answer…"):
                    st.session_state[cache_key] = _transcribe(audio_file)

            transcribed = st.session_state.get(cache_key, "")
            if transcribed:
                st.success("Voice answer transcribed!")
            default_value = transcribed or _DEFAULT_ANSWER
        else:
            default_value = _DEFAULT_ANSWER

        # ── Text answer (pre-filled from transcription if voice was uploaded) ─
        student_answer = st.text_area(
            "Your answer to the coaching question",
            height=150,
            placeholder="Describe a time when you…",
            value=default_value,
        )

        st.divider()
        run_clicked = st.button(
            "🚀 Analyze My Profile",
            use_container_width=True,
            type="primary",
        )

    return UserInputs(
        target_position=target_position,
        resume_file=resume_file,
        transcript_file=transcript_file,
        student_answer=student_answer,
        run_clicked=run_clicked,
    )
