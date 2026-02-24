"""
Orchestrator — run_uniflow
Phase 1: wires mock agent outputs into a FinalReport.
Phase 2+: each mock will be replaced with a real agent .run() call.
"""

from __future__ import annotations

from ai.agents.deps import OrchestratorDeps
from ai.parse_document.parse import parse_resume, parse_transcript
from schemas.agent3 import InterviewResult
from schemas.inputs import ResumeData, TranscriptData
from schemas.report import FinalReport

# ── Parse helpers ─────────────────────────────────────────────────────────────


async def parse_transcript_pdf(path) -> TranscriptData:
    return await parse_transcript(path)


async def parse_resume_pdf(path) -> ResumeData:
    return await parse_resume(path)


# ── Calendar push stub ────────────────────────────────────────────────────────


def push_to_calendar(calendar_service, event):
    """
    Phase 1 stub: no-op.
    Phase 5 will replace with the real Google Calendar API call.
    """
    print(f"[STUB] Would push to Google Calendar: {event.title}")


# ── Main orchestration function ───────────────────────────────────────────────


async def run_uniflow(
    resume_pdf_path,
    transcript_pdf_path,
    target_position: str,
    program_enrolled: str,  # <--- Added
    credits_remaining: int,  # <--- Added
    deps: OrchestratorDeps,
) -> FinalReport:
    """
    Orchestrates the full UniFlow pipeline with degree-specific study plans.
    """
    # ── Step 0: Validation Logic ──────────────────────────────────────────────
    # Check caps based on the degree type prefix (BS vs MS/MBA)
    is_master = any(prefix in program_enrolled for prefix in ["MS", "MBA"])
    is_bachelor = "BS" in program_enrolled

    if is_bachelor and credits_remaining > 120:
        raise ValueError(
            "Invalid input: Bachelor's degrees at SFBU cannot have more than 120 credits remaining."
        )

    if is_master and credits_remaining > 36:
        raise ValueError(
            "Invalid input: Master's degrees at SFBU cannot have more than 36 credits remaining."
        )
    # ── Step 1: Parse inputs ──────────────────────────────────────────────────
    resume_data = await parse_resume_pdf(resume_pdf_path)
    resume_data_json = resume_data.model_dump_json()
    transcript_data = await parse_transcript_pdf(transcript_pdf_path)

    # ── Step 2: Agent 1 — Position Analyst ───────────────────────────────────
    from ai.agents.agent1 import get_position_analyst

    agent1_result = await get_position_analyst().run(target_position)
    position_profile = agent1_result.output

    # ── Step 3: Orchestrator filters Agent 1 output ───────────────────────────
    skill_benchmark = position_profile.must_have
    seniority_level = (
        position_profile.seniority_indicators[0]
        if position_profile.seniority_indicators
        else "mid-level"
    )

    # Populate deps so agent2's search_courses tool has full student context
    deps.resume_text = resume_data_json
    deps.transcript_data = transcript_data
    deps.program_enrolled = program_enrolled
    deps.credits_remaining = credits_remaining
    deps.skill_benchmark = skill_benchmark

    # ── Step 4: Agent 2 — Course & Event Advisor ──────────────────────────────
    from ai.agents.agent2 import get_advisor

    # We inject the study plan data here so the advisor knows the constraints
    agent2_prompt = (
        f"target_position: {target_position}\n"
        f"program_enrolled: {program_enrolled}\n"
        f"credits_remaining: {credits_remaining}\n"
        f"skill_benchmark: {skill_benchmark}\n"
        f"seniority_level: {seniority_level}\n"
        f"resume_text: {resume_data_json}\n"
        f"transcript_data: {transcript_data.model_dump_json()}\n"
    )
    agent2_result = await get_advisor().run(agent2_prompt, deps=deps)
    advisor_report = agent2_result.output

    # ── Step 5: Agent 3 — Interview Coach ─────────────────────────────────────
    from ai.agents.agent3 import evaluate_answer, generate_question
    from schemas.agent3 import StarScores

    top_gap = advisor_report.gap_report.top_gap

    first_question = await generate_question(
        top_gap=top_gap,
        interview_topics=position_profile.interview_topics,
        target_position=target_position,
        previous_results=[],
    )
    interview_result = InterviewResult(
        question=first_question,
        student_answer="",
        star_scores=StarScores(situation=0, task=0, action=0, result=0),
        strengths=[],
        improvements=[],
        stronger_closing="",
    )

    # ── Step 6: Google Calendar push (if opted in) ────────────────────────────
    calendar_synced = False
    if advisor_report.calendar_push_ready and deps.calendar_service:
        for event in advisor_report.event_recs:
            push_to_calendar(deps.calendar_service, event)
        calendar_synced = True

    # ── Step 7: Assemble FinalReport ──────────────────────────────────────────
    return FinalReport(
        student_name=transcript_data.student_name,
        target_position=target_position,
        position_profile=position_profile,
        advisor_report=advisor_report,
        interview_result=interview_result,
        calendar_synced=calendar_synced,
    )
