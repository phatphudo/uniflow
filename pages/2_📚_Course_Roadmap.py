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
courses_per_sem = st.session_state.get("courses_per_semester", 4)
semesters_left = st.session_state.get("semesters_remaining", 3)

st.caption(
    f"Study plan: **{courses_per_sem} courses/semester** · "
    f"**{semesters_left} semesters remaining** · "
    f"Room for up to **{courses_per_sem * semesters_left} more courses**."
)

render_courses(report.advisor_report.course_recs)
