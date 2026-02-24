import html
import streamlit as st
from schemas.agent2 import SemesterPlan


def _e(value) -> str:
    """HTML-escape a value to string."""
    return html.escape(str(value))


def render_courses(study_plan: list[SemesterPlan]) -> None:
    """Render the Course Roadmap panel without code-leakage."""

    if not study_plan:
        st.markdown(
            '<div style="color:#94a3b8;padding:1rem;">No courses found.</div>',
            unsafe_allow_html=True,
        )
        return

    for semester in study_plan:
        label_color = "#a78bfa" if semester.is_final else "#6366f1"
        border_color = "#a78bfa" if semester.is_final else "rgba(99,102,241,0.4)"
        label_tag = " — FINAL SEMESTER" if semester.is_final else ""

        table_rows = ""
        for course in semester.courses:
            # Generate skill badges as a single flat string
            skills_html = "".join(
                [
                    f'<span style="background:rgba(16,185,129,0.1);color:#10b981;border:1px solid #10b981;padding:2px 6px;border-radius:12px;font-size:10px;margin-right:4px;display:inline-block;margin-bottom:4px;">{_e(s)}</span>'
                    for s in course.skills_covered
                ]
            )

            table_rows += (
                f'<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<td style="padding:12px 8px;vertical-align:top;">'
                f'<div style="font-size:0.7rem;color:#94a3b8;font-weight:bold;">{_e(course.course_id)}</div>'
                f'<div style="font-size:0.9rem;color:#f8fafc;font-weight:600;">{_e(course.title)}</div>'
                f"</td>"
                f'<td style="padding:12px 8px;vertical-align:top;color:#94a3b8;font-size:0.85rem;">{_e(course.credits)} cr</td>'
                f'<td style="padding:12px 8px;vertical-align:top;color:#cbd5e1;font-size:0.85rem;line-height:1.4;">{_e(course.relevance_reason)}</td>'
                f'<td style="padding:12px 8px;vertical-align:top;">{skills_html}</td>'
                f"</tr>"
            )

        # The final container must have NO leading indentation in the triple-quoted string
        container_html = f"""
<div style="border-left:4px solid {border_color};background:#0f172a;padding:1.5rem;border-radius:8px;margin-bottom:1.5rem;">
<div style="display:flex;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:0.5rem;">
<span style="color:{label_color};font-weight:800;font-size:0.8rem;letter-spacing:1px;">{_e(semester.semester_label)}{label_tag}</span>
<span style="color:#64748b;font-size:0.8rem;">{_e(semester.total_credits)} Credits Total</span>
</div>
<table style="width:100%;border-collapse:collapse;text-align:left;">
<thead>
<tr style="color:#64748b;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">
<th style="padding:8px;">Class</th>
<th style="padding:8px;">Credits</th>
<th style="padding:8px;">Why Take This</th>
<th style="padding:8px;">Skillsets</th>
</tr>
</thead>
<tbody>{table_rows}</tbody>
</table>
</div>"""

        st.markdown(container_html, unsafe_allow_html=True)