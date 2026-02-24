"""
app/panels/courses.py — Panel 2: Course Roadmap (semester-by-semester).

All dynamic values are HTML-escaped before injection into templates.
"""

import html

import streamlit as st

from schemas.agent2 import SemesterPlan


def _e(value) -> str:
    """HTML-escape a value to string."""
    return html.escape(str(value))


def render_courses(study_plan: list[SemesterPlan]) -> None:
    """Render the Course Roadmap panel organised by semester."""

    if not study_plan:
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
    Practice more skills or update your resume to better match your target position.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    for semester in study_plan:
        label_color = "#a78bfa" if semester.is_final else "#6366f1"
        border_color = "#a78bfa" if semester.is_final else "rgba(99,102,241,0.4)"
        label_tag = " — Final Semester" if semester.is_final else ""

        courses_html = ""
        for course in semester.courses:
            seats_html = (
                f'<span style="color:#4ade80;font-size:0.75rem;">🟢 {_e(course.open_seats)} seats open</span>'
                if course.open_seats
                else ""
            )
            skills_html = "".join(
                f'<span class="badge badge-matched" style="margin:2px">{_e(s)}</span>'
                for s in course.skills_covered
            )
            courses_html += f"""
<div style="padding:0.6rem 0;border-bottom:1px solid rgba(99,102,241,0.1);">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <span style="font-size:0.65rem;color:#64748b;font-weight:600;">{_e(course.course_id)}</span>
      <span style="font-size:0.65rem;color:#475569;margin-left:0.5rem;">{_e(course.category)}</span>
      <div style="font-size:0.95rem;font-weight:600;color:#e2e8f0;margin-top:2px;">{_e(course.title)}</div>
    </div>
    <div style="text-align:right;white-space:nowrap;margin-left:0.5rem;">
      <span style="font-size:0.75rem;color:#94a3b8;">{_e(course.credits)} cr</span><br>
      {seats_html}
    </div>
  </div>
  <div style="color:#94a3b8;font-size:0.8rem;margin-top:0.3rem;">📅 {_e(course.schedule)}</div>
  <div style="color:#c7d2fe;font-size:0.8rem;margin-top:0.2rem;">💡 {_e(course.relevance_reason)}</div>
  <div style="margin-top:0.4rem;">{skills_html}</div>
</div>"""

        st.markdown(
            f"""
<div class="uniflow-card" style="border-left:3px solid {border_color};margin-bottom:0.75rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
    <div style="font-size:0.75rem;color:{label_color};font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">
      {_e(semester.semester_label)}{label_tag}
    </div>
    <div style="font-size:0.75rem;color:#64748b;">{_e(semester.total_credits)} credits</div>
  </div>
  {courses_html}
</div>
""",
            unsafe_allow_html=True,
        )
