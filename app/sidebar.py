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
        resume_file=resume_file,
        transcript_file=transcript_file,
        run_clicked=run_clicked,
    )
