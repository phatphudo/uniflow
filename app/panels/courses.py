"""
app/panels/courses.py — Panel 2: Course Roadmap.

render_courses(course_recs) renders a card per recommended course.
"""

import streamlit as st

from schemas.agent2 import CourseRecommendation


def render_courses(course_recs: list[CourseRecommendation]) -> None:
    """Render the Course Roadmap panel into the current Streamlit column."""
    st.markdown("## 📚 Course Roadmap")

    if not course_recs:
        st.markdown(
            """
<div class="uniflow-card" style="border-left:3px solid #f59e0b;">
    <div style="font-size:0.75rem;color:#f59e0b;font-weight:600;text-transform:uppercase;">
        No Courses Found
    </div>
    <div style="color:#e2e8f0;font-size:0.9rem;margin-top:0.4rem;">
        No matching courses were found in the catalog for your current skill gaps.
    </div>
    <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.4rem;">
        💡 Practice more skills or update your resume to better match your target position.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    for course in course_recs:
        seats_html = (
            f'<span style="color:#4ade80;font-size:0.8rem;">🟢 {course.open_seats} seats open</span>'
            if course.open_seats
            else ""
        )
        skills_html = "".join(
            f'<span class="badge badge-matched" style="margin:2px">{s}</span>'
            for s in course.skills_covered
        )
        st.markdown(
            f"""
<div class="uniflow-card">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
            <div style="font-size:0.7rem;color:#64748b;font-weight:600;">{course.course_id}</div>
            <div style="font-size:1.05rem;font-weight:600;color:#e2e8f0;margin-top:2px;">{course.title}</div>
        </div>
        {seats_html}
    </div>
    <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.5rem;">📅 {course.schedule}</div>
    <div style="color:#c7d2fe;font-size:0.85rem;margin-top:0.4rem;">💡 {course.relevance_reason}</div>
    <div style="margin-top:0.6rem;">{skills_html}</div>
</div>
""",
            unsafe_allow_html=True,
        )
