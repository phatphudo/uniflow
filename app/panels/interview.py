"""
app/panels/interview.py — Panel 4: Interview Feedback.

render_interview(interview_result) renders the coaching question,
student answer, STAR scorecard, and expandable feedback sections.
"""

import streamlit as st

from schemas.agent3 import InterviewResult


def render_interview(ir: InterviewResult) -> None:
    """Render the Interview Feedback panel into the current Streamlit column."""
    st.markdown("## 🎤 Interview Feedback")
    ss = ir.star_scores

    # Question card
    st.markdown(
        f"""
<div class="uniflow-card">
    <div style="font-size:0.7rem;color:#a78bfa;font-weight:600;
                text-transform:uppercase;letter-spacing:0.06em;">Question</div>
    <div style="color:#e2e8f0;font-size:0.9rem;font-style:italic;margin-top:0.3rem;">
        "{ir.question}"
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # TTS: play the question aloud
    try:
        from ai.agents.agent3 import get_question_audio
        audio_bytes = get_question_audio(ir.question)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        pass  # TTS unavailable (no API key or network) — skip silently

    # Answer card
    st.markdown(
        f"""
<div class="uniflow-card">
    <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;
                text-transform:uppercase;letter-spacing:0.06em;">Your Answer</div>
    <div style="color:#cbd5e1;font-size:0.85rem;margin-top:0.3rem;">{ir.student_answer}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # STAR scorecard
    total = ss.total
    st.markdown(
        f"""
<div class="uniflow-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:0.75rem;color:#94a3b8;font-weight:600;text-transform:uppercase;">
            STAR Scorecard
        </div>
        <div style="font-size:1.5rem;font-weight:700;color:#a78bfa;">
            {total}<span style="font-size:0.9rem;color:#64748b"> / 100</span>
        </div>
    </div>
    <div class="star-row">
        <div class="star-box">
            <div class="star-label">Situation</div>
            <div class="star-score">{ss.situation}</div>
            <div class="star-max">/ 25</div>
        </div>
        <div class="star-box">
            <div class="star-label">Task</div>
            <div class="star-score">{ss.task}</div>
            <div class="star-max">/ 25</div>
        </div>
        <div class="star-box">
            <div class="star-label">Action</div>
            <div class="star-score">{ss.action}</div>
            <div class="star-max">/ 25</div>
        </div>
        <div class="star-box">
            <div class="star-label">Result</div>
            <div class="star-score">{ss.result}</div>
            <div class="star-max">/ 25</div>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Expandable feedback sections
    with st.expander("✅ Strengths"):
        for strength in ir.strengths:
            st.markdown(f"- {strength}")

    with st.expander("🔧 Areas to Improve"):
        for improvement in ir.improvements:
            st.markdown(f"- {improvement}")

    with st.expander("💬 Stronger Closing Example"):
        st.markdown(f"*{ir.stronger_closing}*")
