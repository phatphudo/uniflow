"""
app/sidebar.py — Sidebar inputs.

render_sidebar() draws the sidebar and returns a UserInputs dataclass
containing everything the rest of the app needs from the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

PROGRAM_OPTIONS = [
    "Bachelor of Science in Business Administration (BSBA)",
    "Bachelor of Science in Computer Science (BSCS)",
    "Master of Science in Computer Science (MSCS)",
    "Master of Science in Data Science (MSDS)",
    "Master of Science in Electrical Engineering (MSEE)",
]


def _max_credits_for(program: str) -> int:
    return 36 if ("MS" in program or "MBA" in program) else 120


@dataclass
class UserInputs:
    target_position: str
    program_enrolled: str
    credits_remaining: int
    resume_file: Any  # UploadedFile | None
    transcript_file: Any  # UploadedFile | None
    run_clicked: bool


def render_sidebar() -> UserInputs:
    """Render the sidebar UI and return the collected user inputs."""
    with st.sidebar:
        st.markdown("## UniFlow AI")
        st.markdown("*Career Readiness Engine*")
        st.divider()

        target_position = st.text_input(
            "Target Position",
            placeholder="e.g. Product Manager at a tech startup",
            value="Product Manager at a tech startup",
        )

        program_enrolled = st.selectbox(
            "Enrolled Program",
            options=PROGRAM_OPTIONS,
            index=0,
        )

        credits_remaining = st.number_input(
            "Credits Remaining",
            min_value=1,
            max_value=_max_credits_for(program_enrolled),
            value=min(36, _max_credits_for(program_enrolled)),
            step=1,
            help="Total credits you still need to graduate.",
        )

        resume_file = st.file_uploader("Resume (PDF)", type=["pdf"])
        transcript_file = st.file_uploader("Transcript (PDF)", type=["pdf"])

        st.divider()
        run_clicked = st.button(
            "Analyze My Profile",
            use_container_width=True,
            type="primary",
        )

    return UserInputs(
        target_position=target_position,
        program_enrolled=program_enrolled,
        credits_remaining=int(credits_remaining),
        resume_file=resume_file,
        transcript_file=transcript_file,
        run_clicked=run_clicked,
    )
