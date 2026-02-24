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
        def search_courses(ctx: RunContext[OrchestratorDeps], query: str) -> list[dict]:
            """
            Returns the complete semester-by-semester study plan for the student.
            Each item in the list is a SemesterPlan dict with semester_label, courses,
            total_credits, and is_final. Call this exactly once — do not call again.
            Use the returned list directly as study_plan in AdvisorReport.
            """
            import json
            import math
            from retrieval.src.vector_store import query as chroma_query
            from schemas.retrieval import extract_degree_abbr

            _CAPSTONE_IDS = {
                "BSBA": "BUS493", "BSCS": "CS494",
                "MSCS": "CS595", "MSDS": "DS595", "MSEE": "EE595",
            }
            _REQUIREMENTS_PATH = "retrieval/data/processed/requirements.json"

            completed_ids = {c.course_id for c in ctx.deps.transcript_data.completed}
            degree_abbr = extract_degree_abbr(ctx.deps.program_enrolled)
            is_master = any(p in ctx.deps.program_enrolled for p in ["MS", "MBA"])
            min_credits = 9 if is_master else 12
            position_query = " ".join(ctx.deps.skill_benchmark[:3]) if ctx.deps.skill_benchmark else query

            # ── 1. Load requirements.json and find the degree ────────────────────
            with open(_REQUIREMENTS_PATH) as f:
                all_degrees = json.load(f)

            degree_data = next(
                (d for d in all_degrees if d["degree_name"] == ctx.deps.program_enrolled),
                None,
            )

            courses: list[dict] = []
            picked_ids: set[str] = set(completed_ids)

            if degree_data:
                # ── 2. Walk each category and apply pick-all vs pick-relevant ────
                for cat in degree_data.get("course_requirements", []):
                    cat_name = cat.get("category", "General")
                    cat_courses = cat.get("courses", [])
                    credits_required = float(cat.get("credits_required", 0))

                    # Skip empty categories (Electives) — handled in step 3
                    if not cat_courses:
                        continue

                    # Remove already-completed courses
                    remaining = [c for c in cat_courses if c["code"] not in picked_ids]

                    all_mandatory = (credits_required == len(cat_courses) * 3)

                    if all_mandatory:
                        # All courses are required — pick every remaining one
                        for course in remaining:
                            cr = float(course.get("credits", 3))
                            courses.append({
                                "course_id": course["code"],
                                "title": course["title"],
                                "category": cat_name,
                                "credits": cr,
                                "relevance_reason": f"Required for {cat_name}",
                                "skills_covered": [],
                                "schedule": "See course catalog for schedule",
                            })
                            picked_ids.add(course["code"])
                    else:
                        # Pick relevant courses until credits_required is met
                        # Use ChromaDB to rank by relevance to position role
                        catalog_results = chroma_query(position_query, "courses", k=50)
                        ranked_ids = [r.get("course_id", "") for r in catalog_results]

                        # Build a relevance-ordered list: ranked first, then unranked
                        remaining_codes = {c["code"] for c in remaining}
                        remaining_map = {c["code"]: c for c in remaining}

                        ordered = []
                        for rid in ranked_ids:
                            if rid in remaining_codes:
                                ordered.append(remaining_map[rid])
                                remaining_codes.discard(rid)
                        # Append any courses not found in ChromaDB ranking
                        for code in remaining_codes:
                            ordered.append(remaining_map[code])

                        # Already-completed credits count toward credits_required
                        completed_in_cat = [c for c in cat_courses if c["code"] in completed_ids]
                        filled = sum(float(c.get("credits", 3)) for c in completed_in_cat)

                        for course in ordered:
                            if filled >= credits_required:
                                break
                            cr = float(course.get("credits", 3))
                            courses.append({
                                "course_id": course["code"],
                                "title": course["title"],
                                "category": cat_name,
                                "credits": cr,
                                "relevance_reason": f"Selected for {cat_name} (aligned with target role)",
                                "skills_covered": [],
                                "schedule": "See course catalog for schedule",
                            })
                            picked_ids.add(course["code"])
                            filled += cr

            required_credits = sum(c["credits"] for c in courses)
            print(f"\n[search_courses] {len(courses)} requirement courses ({required_credits} cr) for {degree_abbr}")

            # ── 3. Fill Elective credits from catalog ────────────────────────────
            extra_credits = ctx.deps.credits_remaining - required_credits
            if extra_credits > 0:
                catalog = chroma_query(position_query, "courses", k=30)
                for course in catalog:
                    if extra_credits <= 0:
                        break
                    cid = course.get("course_id", "")
                    cr = float(course.get("credits", 3))
                    if cid and cid not in picked_ids and cr <= extra_credits:
                        courses.append({
                            "course_id": cid,
                            "title": course.get("title", ""),
                            "category": "Elective",
                            "credits": cr,
                            "relevance_reason": f"Elective aligned with target role",
                            "skills_covered": course.get("skills_taught", []),
                            "schedule": course.get("schedule", "See course catalog for schedule"),
                        })
                        picked_ids.add(cid)
                        extra_credits -= cr

            # ── 3. Separate capstone from the rest ───────────────────────────────
            capstone_id = _CAPSTONE_IDS.get(degree_abbr)
            capstone = [c for c in courses if c["course_id"] == capstone_id]
            non_capstone = [c for c in courses if c["course_id"] != capstone_id]

            # ── 4. Greedy semester packing ───────────────────────────────────────
            # Fill each semester to >= min_credits, last semester gets the remainder.
            n_semesters = max(1, math.ceil(ctx.deps.credits_remaining / min_credits))
            semesters: list[list[dict]] = [[] for _ in range(n_semesters)]
            sem_credits: list[float] = [0.0] * n_semesters

            sem_idx = 0
            for course in non_capstone:
                cr = course["credits"]
                semesters[sem_idx].append(course)
                sem_credits[sem_idx] += cr
                # Advance to next semester once current meets minimum (unless last)
                if sem_credits[sem_idx] >= min_credits and sem_idx < n_semesters - 1:
                    sem_idx += 1

            # Always place capstone in the final semester
            for c in capstone:
                semesters[-1].append(c)
                sem_credits[-1] += c["credits"]

            # ── 5. Build SemesterPlan dicts ──────────────────────────────────────
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

            print(f"\n[search_courses] {len(courses)} courses → {total} semesters")
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
