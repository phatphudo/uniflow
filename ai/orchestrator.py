"""
Orchestrator — run_uniflow
Phase 1: wires mock agent outputs into a FinalReport.
Phase 2+: each mock will be replaced with a real agent .run() call.
"""

from __future__ import annotations

from ai.agents.agent1 import MOCK_POSITION_PROFILE
from ai.agents.agent2 import MOCK_ADVISOR_REPORT
from ai.agents.agent3 import MOCK_INTERVIEW_RESULT
from ai.parse_document.parse import parse_resume, parse_transcript
from ai.agents.deps import OrchestratorDeps
from schemas.inputs import TranscriptCourse, TranscriptData, ResumeData
from schemas.report import FinalReport

# ── Phase 1 — Transcript stub parser ─────────────────────────────────────────


async def parse_transcript_pdf(path) -> TranscriptData:
    """
    Phase 1 stub: returns dummy TranscriptData.
    Phase 3 will replace with real pdfplumber extraction.
    """
    return await parse_transcript(path)
    # TranscriptData(
    #     student_name="Alex Rivera",
    #     gpa=3.4,
    #     completed=[
    #         TranscriptCourse(
    #             course_id="CS-101",
    #             title="Intro to Programming",
    #             grade="A",
    #             credits=3.0,
    #             semester="Fall 2022",
    #         ),
    #         TranscriptCourse(
    #             course_id="BUS-201",
    #             title="Principles of Management",
    #             grade="B+",
    #             credits=3.0,
    #             semester="Spring 2023",
    #         ),
    #         TranscriptCourse(
    #             course_id="MATH-101",
    #             title="Calculus I",
    #             grade="B",
    #             credits=4.0,
    #             semester="Fall 2022",
    #         ),
    #     ],
    #     in_progress=[
    #         TranscriptCourse(
    #             course_id="CS-301",
    #             title="Software Engineering",
    #             grade="IP",
    #             credits=3.0,
    #             semester="Spring 2026",
    #         ),
    #     ],
    # )

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
    resume_pdf_path,   # UploadedFile | str | None
    transcript_pdf_path,  # UploadedFile | str | None
    target_position: str,
    deps: OrchestratorDeps,
    student_answer: str,
    use_mocks: bool = False,  # Phase 1: True; Phase 6: False
) -> FinalReport:
    """
    Orchestrates the full UniFlow pipeline.

    Phase 1: All agents return hardcoded mock data. `use_mocks=True`.
    Each phase replaces one block with a real agent call:
      Phase 2: Agent 1 block
      Phase 4: Agent 2 block
      Phase 5: Agent 3 block + Calendar push
    """

    # ── Step 1: Parse inputs ──────────────────────────────────────────────────
    if use_mocks:
        resume_data_json = "[MOCK RESUME] Senior PM with 2 years experience in B2B SaaS."
        transcript_data = await parse_transcript_pdf(transcript_pdf_path)
    else:
        resume_data = await parse_resume_pdf(resume_pdf_path)
        resume_data_json = resume_data.model_dump_json()
        transcript_data = await parse_transcript_pdf(transcript_pdf_path)

    # ── Step 2: Agent 1 — Position Analyst ───────────────────────────────────
    if use_mocks:
        position_profile = MOCK_POSITION_PROFILE
    else:
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

    # ── Step 4: Agent 2 — Course & Event Advisor ──────────────────────────────
    if use_mocks:
        advisor_report = MOCK_ADVISOR_REPORT
    else:
        from ai.agents.agent2 import get_advisor

        agent2_prompt = (
            f"skill_benchmark: {skill_benchmark}\n"
            f"seniority_level: {seniority_level}\n"
            f"resume_text: {resume_data_json}\n"
            f"transcript_data: {transcript_data.model_dump_json()}\n"
            f"target_position: {target_position}\n"
        )
        agent2_result = await get_advisor().run(agent2_prompt, deps=deps)
        advisor_report = agent2_result.output 

    # ── Step 5: Agent 3 — Interview Coach ────────────────────────────────────
    if use_mocks:
        interview_result = MOCK_INTERVIEW_RESULT
    else:
        from ai.agents.agent3 import get_interview_coach

        top_gap = advisor_report.gap_report.top_gap
        agent3_prompt = (
            f"top_gap: {top_gap}\n"
            f"interview_topics: {position_profile.interview_topics}\n"
            f"position_context: {target_position}\n"
            f"student_answer: {student_answer}\n"
        )
        agent3_result = await get_interview_coach().run(agent3_prompt)
        interview_result = agent3_result.output

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
