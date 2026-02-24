"""
Retriever agent — LLM-driven course selection using retriever_prompt.md.

Tool design:
  - get_all_courses: returns the COMPLETE list of courses the student still needs
    (all required courses + electives to fill remaining credits), computed entirely
    in Python using ChromaDB for ranking.  The LLM calls this once and outputs
    the list verbatim — no enumeration or credit-counting left to the LLM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic_ai import Agent, ModelRetry, RunContext

from ai.prompts import load_prompt
from config import settings
from retrieval.src.vector_store import query as chroma_query

_SYSTEM_PROMPT = load_prompt("retrierver_prompt")
_REQUIREMENTS_PATH = "retrieval/data/processed/requirements.json"

_agent = None


@dataclass
class RetrieverDeps:
    program_enrolled: str = ""
    completed_ids: set[str] = field(default_factory=set)
    credits_remaining: int = 0
    skill_benchmark: list[str] = field(default_factory=list)
    student_skills: list[str] = field(default_factory=list)


def agent():
    """Return the retrieval agent, creating it on first call."""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=settings.ai_model,
            system_prompt=_SYSTEM_PROMPT,
            deps_type=RetrieverDeps,
            output_type=list[dict],
            output_retries=3,
        )

        @_agent.output_validator
        async def validate_result(ctx: RunContext[RetrieverDeps], result: list[dict]) -> list[dict]:
            if not result:
                raise ModelRetry(
                    "Output is empty. You MUST call get_all_courses with the "
                    "enrolled_program string first, then output the returned list."
                )
            return result

        @_agent.tool
        def get_all_courses(ctx: RunContext[RetrieverDeps], enrolled_program: str) -> list[dict]:
            """
            Returns the complete list of courses the student still needs for their degree.
            Includes ALL required courses (mandatory categories fully, selection categories
            pre-ranked by ChromaDB) plus enough electives to fill remaining credits.

            Call this EXACTLY ONCE. Use the returned list directly as your output —
            do not add, remove, or reorder any course.
            """
            with open(_REQUIREMENTS_PATH) as f:
                all_degrees = json.load(f)

            # Always use the exact program name from deps (Streamlit dropdown value)
            # instead of the LLM-provided argument, which may be reformatted.
            query = ctx.deps.program_enrolled.strip()
            print(f"[get_all_courses] Using program from deps: {query}")

            # Exact match against degree_name in requirements.json
            degree_data = next(
                (d for d in all_degrees if d["degree_name"] == query),
                None,
            )

            if degree_data is None:
                print(f"[get_all_courses] No degree match for: {query}")
                return []

            completed = ctx.deps.completed_ids
            position_query = (
                " ".join(ctx.deps.skill_benchmark[:3])
                if ctx.deps.skill_benchmark else enrolled_program
            )

            all_courses: list[dict] = []
            picked_ids: set[str] = set(completed)

            # ── 1. Required courses (mandatory + selection categories) ──────────
            for cat in degree_data.get("course_requirements", []):
                cat_name = cat.get("category", "General")
                cat_courses = cat.get("courses", [])
                credits_required = float(cat.get("credits_required", 0))

                if not cat_courses:
                    continue

                remaining = [c for c in cat_courses if c["code"] not in picked_ids]
                # Use actual credits (labs = 1 cr, regular = 3 cr)
                actual_cat_credits = sum(float(c.get("credits", 3)) for c in cat_courses)
                all_mandatory = (credits_required >= actual_cat_credits)

                if all_mandatory:
                    # Include every remaining course in this category
                    for c in remaining:
                        all_courses.append({
                            "course_id": c["code"],
                            "title": c["title"],
                            "category": cat_name,
                            "credits": float(c.get("credits", 3)),
                            "relevance_reason": f"Required for {cat_name}",
                            "skills_covered": [],
                            "schedule": "See course catalog for schedule",
                        })
                        picked_ids.add(c["code"])
                else:
                    # Pre-rank by ChromaDB relevance, pick until credits_required met
                    catalog_results = chroma_query(position_query, "courses", k=50)
                    ranked_ids = [r.get("course_id", "") for r in catalog_results]

                    remaining_map = {c["code"]: c for c in remaining}
                    ordered: list[dict] = []
                    seen: set[str] = set()
                    for rid in ranked_ids:
                        if rid in remaining_map and rid not in seen:
                            ordered.append(remaining_map[rid])
                            seen.add(rid)
                    for c in remaining:
                        if c["code"] not in seen:
                            ordered.append(c)

                    completed_credits_in_cat = sum(
                        float(c.get("credits", 3))
                        for c in cat_courses if c["code"] in completed
                    )
                    filled = completed_credits_in_cat

                    for c in ordered:
                        if filled >= credits_required:
                            break
                        cr = float(c.get("credits", 3))
                        all_courses.append({
                            "course_id": c["code"],
                            "title": c["title"],
                            "category": cat_name,
                            "credits": cr,
                            "relevance_reason": f"Selected for {cat_name} (aligned with target role)",
                            "skills_covered": [],
                            "schedule": "See course catalog for schedule",
                        })
                        picked_ids.add(c["code"])
                        filled += cr

            # ── 2. Electives to fill remaining credit gap ───────────────────────
            required_credits = sum(c["credits"] for c in all_courses)
            elective_credits_needed = ctx.deps.credits_remaining - required_credits

            print(
                f"[get_all_courses] {len(all_courses)} required courses "
                f"({required_credits} cr), elective gap: {elective_credits_needed} cr"
            )

            if elective_credits_needed > 0:
                # Electives target skills the student is MISSING (benchmark − current)
                student_lower = {s.lower() for s in ctx.deps.student_skills}
                missing_skills = [
                    s for s in ctx.deps.skill_benchmark
                    if s.lower() not in student_lower
                ]
                elective_query = (
                    " ".join(missing_skills) if missing_skills
                    else position_query
                )
                print(f"[get_all_courses] Elective query (missing skills): {elective_query}")
                elective_results = chroma_query(elective_query, "courses", k=30)
                elective_added = 0.0
                for r in elective_results:
                    if elective_added >= elective_credits_needed:
                        break
                    cid = r.get("course_id", "")
                    if not cid or cid in picked_ids:
                        continue
                    cr = float(r.get("credits", 3))
                    all_courses.append({
                        "course_id": cid,
                        "title": r.get("title", ""),
                        "category": "Elective",
                        "credits": cr,
                        "relevance_reason": "Elective aligned with target role",
                        "skills_covered": [],
                        "schedule": "See course catalog for schedule",
                    })
                    picked_ids.add(cid)
                    elective_added += cr

            total_credits = sum(c["credits"] for c in all_courses)
            print(
                f"[get_all_courses] Total: {len(all_courses)} courses, "
                f"{total_credits} cr (target: {ctx.deps.credits_remaining} cr)"
            )
            return all_courses

    return _agent
