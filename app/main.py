"""
app/main.py — Application entry point.

Assembles config, sidebar, runner, and panels into the full Streamlit UI.
This is the only file that imports from all sub-modules.
"""

import streamlit as st

from app.config import configure_page, inject_css
from app.panels.benchmark import render_benchmark
from app.panels.courses import render_courses
from app.panels.events import render_events
from app.panels.interview import render_interview
from app.runner import run_analysis
from app.sidebar import render_sidebar


def run_app() -> None:
    """Entry point — call this from the root app.py."""
    # ── 1. Page setup (must be first st call) ─────────────────────────────────
    configure_page()
    inject_css()

    # ── 2. Sidebar inputs ─────────────────────────────────────────────────────
    inputs = render_sidebar()

    # ── 3. Header ─────────────────────────────────────────────────────────────
    st.markdown("# 🎓 UniFlow AI — Career Readiness Report")
    st.caption(
        "Upload your resume and transcript, set a target role, "
        "and get your career gap analysis in seconds."
    )

    if not inputs.run_clicked:
        st.info(
            "👈 Fill in your details on the left and click **Analyze My Profile** to begin."
        )
        return

    # ── 4. Run orchestrator ───────────────────────────────────────────────────
    report = run_analysis(inputs)

    # ── 5. Top row: Benchmark (left) + Courses (right) ────────────────────────
    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        render_benchmark(report.advisor_report.gap_report)
    with col_right:
        render_courses(report.advisor_report.course_recs)

    st.divider()

    # ── 6. Bottom row: Events (left) + Interview (right) ──────────────────────
    col3, col4 = st.columns([1, 1], gap="large")
    with col3:
        render_events(
            event_recs=report.advisor_report.event_recs,
            calendar_push_ready=report.advisor_report.calendar_push_ready,
        )
    with col4:
        render_interview(report.interview_result)

    # ── 7. Footer ─────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        f"Report for **{report.student_name}** · "
        f"Target: **{report.target_position}** · "
        f"Benchmark: **{report.benchmark_score}/100** · "
        f"Interview: **{report.interview_score}/100** · "
        f"Calendar synced: {'✅' if report.calendar_synced else '⏳ Phase 5'} · "
        f"*UniFlow AI v1.0 — Phase 1 Skeleton*"
    )
