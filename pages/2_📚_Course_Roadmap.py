"""
Page 3 — Course Roadmap
Reads the FinalReport from st.session_state and renders the courses panel.
Also displays the student's study plan (courses/semester, semesters remaining).
"""

import streamlit as st

from app.config import configure_page, inject_css
from app.panels.courses import render_courses

configure_page()
inject_css()

st.markdown("# 📚 Course Roadmap")

if "report" not in st.session_state:
    st.warning("No report yet. Go to the **Home** page and run an analysis first.")
    st.stop()

report = st.session_state["report"]
study_plan = report.advisor_report.study_plan

total_semesters = len(study_plan)
total_credits = sum(s.total_credits for s in study_plan)
total_courses = sum(len(s.courses) for s in study_plan)

st.caption(
    f"Study plan: **{total_semesters} semester{'s' if total_semesters != 1 else ''}** · "
    f"**{total_courses} courses** · "
    f"**{total_credits} credits**"
)

render_courses(study_plan)
