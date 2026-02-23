"""
app/panels/interview.py — Panel 4: Interview Coach (multi-turn chat).

render_interview_chat(report, run_async) manages a stateful interview session:
  - Shows previous rounds (question -> answer -> STAR feedback) as expandable cards.
  - Displays the current pending question (with optional TTS audio).
  - Accepts a typed or voice-uploaded answer.
  - On "Submit Answer": evaluates via agent3, then auto-generates the next question.
  - On "End Session": shows a summary and allows restarting.

State lives in st.session_state keyed by the first question so it resets when
a new analysis is run.
"""

import streamlit as st

from schemas.agent3 import InterviewResult
from schemas.report import FinalReport


# ── Helpers ───────────────────────────────────────────────────────────────────

def _star_card(ir: InterviewResult, round_num: int) -> None:
    """Render a completed interview round as a collapsible card."""
    ss = ir.star_scores
    total = ss.total
    label = f"Round {round_num} — {ir.question[:55]}{'...' if len(ir.question) > 55 else ''} | {total}/100"
    with st.expander(label, expanded=False):
        st.markdown(
            f"""<div class="uniflow-card">
    <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;
                text-transform:uppercase;letter-spacing:0.06em;">Your Answer</div>
    <div style="color:#cbd5e1;font-size:0.85rem;margin-top:0.3rem;">{ir.student_answer}</div>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="uniflow-card">
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
</div>""",
            unsafe_allow_html=True,
        )
        if ir.strengths:
            with st.expander("Strengths"):
                for s in ir.strengths:
                    st.markdown(f"- {s}")
        if ir.improvements:
            with st.expander("Areas to Improve"):
                for s in ir.improvements:
                    st.markdown(f"- {s}")
        if ir.stronger_closing:
            with st.expander("Stronger Closing Example"):
                st.markdown(f"*{ir.stronger_closing}*")


def _transcribe(audio_file, cache_key: str) -> str:
    """Transcribe an uploaded audio file, caching the result in session_state."""
    if cache_key not in st.session_state:
        with st.spinner("Transcribing audio..."):
            try:
                from ai.agents.agent3 import get_openai_client
                from config import settings
                tr = get_openai_client().audio.transcriptions.create(
                    model=settings.stt_model,
                    file=audio_file,
                )
                st.session_state[cache_key] = (tr.text or "").strip()
            except Exception as e:
                st.error(f"Transcription failed: {e}")
                st.session_state[cache_key] = ""
    return st.session_state[cache_key]


# ── Main render function ──────────────────────────────────────────────────────

def render_interview_chat(report: FinalReport, run_async) -> None:
    """Render the multi-turn Interview Coach panel."""
    st.markdown("## Interview Coach")

    # Initialise session state for this report.
    # Use the first question as a stable key so state resets on new analysis.
    report_key = report.interview_result.question
    if st.session_state.get("_interview_report_key") != report_key:
        st.session_state._interview_report_key = report_key
        st.session_state.interview_history = []
        st.session_state.interview_current_q = report_key
        st.session_state.interview_ended = False

    history: list[InterviewResult] = st.session_state.interview_history
    current_q: str = st.session_state.interview_current_q
    ended: bool = st.session_state.interview_ended

    # ── Render previous rounds ────────────────────────────────────────────────
    for i, ir in enumerate(history, 1):
        _star_card(ir, i)

    # ── Session ended ─────────────────────────────────────────────────────────
    if ended:
        if history:
            avg = sum(ir.star_scores.total for ir in history) // len(history)
            st.success(
                f"Session complete! Average STAR score: **{avg}/100** over {len(history)} round(s)."
            )
        else:
            st.info("Session ended. No rounds were completed.")

        if st.button("Start New Session", key="interview_restart"):
            st.session_state.interview_history = []
            st.session_state.interview_current_q = report_key
            st.session_state.interview_ended = False
            st.rerun()
        return

    # ── Current question ──────────────────────────────────────────────────────
    round_num = len(history) + 1
    st.markdown(
        f"""<div class="uniflow-card" style="border-left:3px solid #a78bfa;">
    <div style="font-size:0.7rem;color:#a78bfa;font-weight:600;
                text-transform:uppercase;letter-spacing:0.06em;">
        Question {round_num}
    </div>
    <div style="color:#e2e8f0;font-size:0.9rem;font-style:italic;margin-top:0.3rem;">
        "{current_q}"
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Optional TTS audio
    try:
        from ai.agents.agent3 import get_question_audio
        audio_bytes = get_question_audio(current_q)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        pass  # TTS unavailable - skip silently

    # ── Answer input ──────────────────────────────────────────────────────────
    st.markdown("#### Your Answer")

    audio_file = st.audio_input(
        "Record your answer",
        key=f"audio_record_r{round_num}",
    )

    answer_key = f"answer_r{round_num}"
    if audio_file:
        cache_key = f"stt_r{round_num}_{audio_file.name}_{audio_file.size}"
        transcribed = _transcribe(audio_file, cache_key)
        if transcribed:
            st.session_state[answer_key] = transcribed

    student_answer = st.text_area(
        "Type or edit your answer",
        height=150,
        placeholder="Describe a time when...  (use the STAR format)",
        key=answer_key,
    )

    # ── Action buttons ────────────────────────────────────────────────────────
    col_submit, col_end = st.columns([3, 1])

    with col_submit:
        submit = st.button("Submit Answer", type="primary", key=f"submit_r{round_num}")
    with col_end:
        end = st.button("End Session", key=f"end_r{round_num}")

    if end:
        st.session_state.interview_ended = True
        st.rerun()

    if submit:
        if not student_answer.strip():
            st.warning("Please provide an answer before submitting.")
            return

        from ai.agents.agent3 import evaluate_answer, generate_question

        top_gap = report.advisor_report.gap_report.top_gap
        topics = report.position_profile.interview_topics
        position = report.target_position

        # Step 1: evaluate the current answer
        with st.spinner("Evaluating your answer..."):
            try:
                result: InterviewResult = run_async(
                    evaluate_answer(
                        question=current_q,
                        student_answer=student_answer.strip(),
                        top_gap=top_gap,
                        interview_topics=topics,
                        target_position=position,
                        previous_results=history,
                    )
                )
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                return

        st.session_state.interview_history.append(result)

        # Step 2: generate the next question
        with st.spinner("Preparing next question..."):
            try:
                next_q: str = run_async(
                    generate_question(
                        top_gap=top_gap,
                        interview_topics=topics,
                        target_position=position,
                        previous_results=st.session_state.interview_history,
                    )
                )
                st.session_state.interview_current_q = next_q
            except Exception as e:
                st.error(f"Question generation failed: {e}")
                return

        st.rerun()
