"""
Agent 2 — Course & Event Advisor
Phase 1: MOCK_ADVISOR_REPORT used for the skeleton demo.
Phase 4: call get_advisor().run(..., deps=deps) for real LLM + RAG + web search.

System prompt is loaded from ai/prompts/agent2_advisor.md for easy versioning.
Agent and tools are defined lazily so Phase 1 runs without API keys.
"""

from __future__ import annotations

import httpx
from pydantic_ai import Agent, RunContext

from ai.agents.deps import OrchestratorDeps
from ai.prompts import load_prompt
from config import settings
from schemas.agent2 import AdvisorReport

# Loaded from disk — edit ai/prompts/agent2_advisor.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent2_advisor")
_advisor = None


def get_advisor():
    """Return the PydanticAI Advisor agent, creating it on first call."""
    global _advisor
    if _advisor is None:
        _advisor = Agent(
            model=settings.ai_model,
            output_type=AdvisorReport,
            deps_type=OrchestratorDeps,
            system_prompt=_SYSTEM_PROMPT,
            output_retries=3,
        )
        @_advisor.tool
        async def search_courses(ctx: RunContext[OrchestratorDeps], query: str) -> list[dict]:
            """
            Returns the complete semester-by-semester study plan for the student.
            Each item in the list is a SemesterPlan dict with semester_label, courses,
            total_credits, and is_final. Call this exactly once — do not call again.
            Use the returned list directly as study_plan in AdvisorReport.
            """
            import math
            from retrieval.src.retriever import agent as retriever_agent
            from schemas.retrieval import extract_degree_abbr

            _CAPSTONE_IDS = {
                "BSBA": "BUS493", "BSCS": "CS494",
                "MSCS": "CS595", "MSDS": "DS595", "MSEE": "EE595",
            }

            completed_ids = {c.course_id for c in ctx.deps.transcript_data.completed}
            degree_abbr = extract_degree_abbr(ctx.deps.program_enrolled)
            is_master = any(p in ctx.deps.program_enrolled for p in ["MS", "MBA"])
            min_credits = 9 if is_master else 12

            # ── 1. Call the retriever sub-agent to get the flat course list ──────
            from retrieval.src.retriever import RetrieverDeps

            # Extract student's current skills from resume for gap-based elective selection
            import json as _json
            try:
                resume_obj = _json.loads(ctx.deps.resume_text)
                student_skills = resume_obj.get("skills", [])
            except (ValueError, AttributeError):
                student_skills = []

            retriever_deps = RetrieverDeps(
                program_enrolled=ctx.deps.program_enrolled,
                completed_ids=completed_ids,
                credits_remaining=ctx.deps.credits_remaining,
                skill_benchmark=ctx.deps.skill_benchmark,
                student_skills=student_skills,
            )
            user_prompt = (
                f"enrolled_program: {ctx.deps.program_enrolled}\n"
                f"completed_courses: {sorted(completed_ids)}\n"
                f"credits_remaining: {ctx.deps.credits_remaining}\n"
                f"skill_benchmark: {ctx.deps.skill_benchmark}\n"
            )
            result = await retriever_agent().run(user_prompt, deps=retriever_deps)
            # Retriever output_type=list[dict] — already parsed and validated
            # Safety net: strip any completed courses that slipped through
            courses: list[dict] = [
                c for c in (result.output or [])
                if c.get("course_id") not in completed_ids
            ]

            print(f"\n[search_courses] Retriever returned {len(courses)} courses")

            # ── 2. Separate capstone from the rest ──────────────────────────────
            capstone_id = _CAPSTONE_IDS.get(degree_abbr)
            capstone = [c for c in courses if c.get("course_id") == capstone_id]
            non_capstone = [c for c in courses if c.get("course_id") != capstone_id]

            # ── 3. Greedy semester packing ──────────────────────────────────────
            total_credits = sum(float(c.get("credits", 3)) for c in courses)
            n_semesters = max(1, math.ceil(total_credits / min_credits))
            semesters: list[list[dict]] = [[] for _ in range(n_semesters)]
            sem_credits: list[float] = [0.0] * n_semesters

            sem_idx = 0
            for course in non_capstone:
                cr = float(course.get("credits", 3))
                semesters[sem_idx].append(course)
                sem_credits[sem_idx] += cr
                if sem_credits[sem_idx] >= min_credits and sem_idx < n_semesters - 1:
                    sem_idx += 1

            # Always place capstone in the final semester
            for c in capstone:
                semesters[-1].append(c)
                sem_credits[-1] += float(c.get("credits", 3))

            # ── 4. Build SemesterPlan dicts ─────────────────────────────────────
            study_plan = []
            total = len(semesters)
            for i, (sem_courses, s_credits) in enumerate(zip(semesters, sem_credits)):
                is_final = (i == total - 1)
                study_plan.append({
                    "semester_label": "Final Semester" if is_final else f"Semester {i + 1}",
                    "courses": sem_courses,
                    "total_credits": round(s_credits, 1),
                    "is_final": is_final,
                })

            print(f"[search_courses] {len(courses)} courses → {total} semesters")
            for sp in study_plan:
                print(f"  {sp['semester_label']}: {len(sp['courses'])} courses, {sp['total_credits']} cr")
            return study_plan

        @_advisor.tool
        async def search_events(
            ctx: RunContext[OrchestratorDeps], query: str
        ) -> list[dict]:
            """Live web search for professional events via Serper API."""
            if not ctx.deps.search_api_key:
                return []
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://google.serper.dev/search",
                        headers={"X-API-KEY": ctx.deps.search_api_key},
                        json={"q": query, "num": 10},
                    )
                    resp.raise_for_status()
                    return resp.json().get("organic", [])
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"Serper API error {e.response.status_code}: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise RuntimeError(f"Serper API request failed: {e}") from e

    return _advisor
