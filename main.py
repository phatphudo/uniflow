"""
main.py — UniFlow AI Home Page
Page 1 of 5: upload inputs, set parameters, trigger analysis.
Results are cached in st.session_state so all other pages can read them.
"""

import streamlit as st

from ai.orchestrator import run_uniflow
from app.config import configure_page, inject_css
from app.runner import build_stub_deps, run_async

configure_page()
inject_css()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🎓 UniFlow AI")
st.markdown(
    "**Career Readiness Engine** — Upload your resume and transcript, "
    "set your target role and study plan, and get a complete readiness report "
    "with skill gap analysis, course roadmap, networking events, and live interview coaching."
)
st.divider()

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("input_form"):
    st.markdown("### Your Profile")

    target_position = st.text_input(
        "Target Position",
        placeholder="e.g. Product Manager at a tech startup",
        value=st.session_state.get(
            "target_position", "Product Manager at a tech startup"
        ),
    )

    col1, col2 = st.columns(2)
    with col1:
        resume_file = st.file_uploader("Resume (PDF)", type=["pdf"])
    with col2:
        transcript_file = st.file_uploader("Academic Transcript (PDF)", type=["pdf"])

    st.markdown("### Study Plan")
    col3, col4 = st.columns(2)
    with col3:
        courses_per_semester = st.number_input(
            "Courses per semester",
            min_value=1,
            max_value=8,
            value=st.session_state.get("courses_per_semester", 3),
            help="How many courses can you take each semester?",
        )
    with col4:
        semesters_remaining = st.number_input(
            "Semesters remaining",
            min_value=1,
            max_value=12,
            value=st.session_state.get("semesters_remaining", 2),
            help="How many full semesters do you have left until graduation?",
        )

    submitted = st.form_submit_button(
        "🚀 Analyze My Profile", type="primary", use_container_width=True
    )

# ── Run analysis ──────────────────────────────────────────────────────────────
if submitted:
    if not resume_file or not transcript_file:
        st.error("Please upload both your Resume and Academic Transcript PDFs.")
    else:
        # Persist study plan inputs in session_state for other pages to access
        st.session_state["target_position"] = target_position
        st.session_state["courses_per_semester"] = int(courses_per_semester)
        st.session_state["semesters_remaining"] = int(semesters_remaining)

        deps = build_stub_deps()
        with st.spinner("Analyzing your profile — this may take up to 30 seconds..."):
            try:
                report = run_async(
                    run_uniflow(
                        resume_pdf_path=resume_file,
                        transcript_pdf_path=transcript_file,
                        target_position=target_position,
                        deps=deps,
                    )
                )
                st.session_state["report"] = report
                st.success(
                    "✅ Analysis complete! Navigate to the pages on the left to explore your report."
                )
            except Exception as e:
                st.error(f"Analysis failed: {e}")

# ── Status ────────────────────────────────────────────────────────────────────
if "report" in st.session_state:
    report = st.session_state["report"]
    st.divider()
    st.markdown("### 📋 Report Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Student", report.student_name)
    m2.metric("Target Role", report.target_position)
    m3.metric("Benchmark Score", f"{report.benchmark_score} / 100")
    m4.metric("Interview Score", f"{report.interview_score} / 100")
    st.info(
        "Use the sidebar to navigate to **Resume Benchmark**, **Course Roadmap**, "
        "**Events to Attend**, and **Interview Coach**."
    )
else:
    st.info("Fill in your details above and click **Analyze My Profile** to begin.")
