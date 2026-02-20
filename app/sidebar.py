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
        student_answer = st.text_area(
            "Your answer to the coaching question",
            height=150,
            placeholder="Describe a time when you...",
            value=(
                "In my internship I helped the team decide which features to ship for Q3. "
                "I talked to a few users and wrote up my recommendations. The team liked them "
                "and we shipped on time."
            ),
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
