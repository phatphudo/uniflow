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
            Returns all courses the student still needs to complete their degree,
            plus elective courses from the catalog if extra credits remain.
            Call this exactly once — it returns the complete course list.
            """
            import json
            from retrieval.src.vector_store import query as chroma_query

            completed_ids = {c.course_id for c in ctx.deps.transcript_data.completed}

            # Step 1: Pull degree requirements from ChromaDB
            degree_results = chroma_query(ctx.deps.program_enrolled, "requirements", k=1)
            remaining: list[dict] = []
            required_credits = 0.0

            if degree_results:
                for category in degree_results[0].get("course_requirements", []):
                    cat_name = category.get("category", "General")
                    for course in category.get("courses", []):
                        if course["code"] not in completed_ids:
                            remaining.append({
                                "course_id": course["code"],
                                "title": course["title"],
                                "category": cat_name,
                                "credits": course.get("credits", 3),
                                "relevance_reason": f"Required for {cat_name}",
                                "skills_covered": [],
                                "schedule": "See course catalog for schedule",
                            })
                            required_credits += course.get("credits", 3)

            # Step 2: Fill remaining credits with catalog electives if room exists
            extra_credits = ctx.deps.credits_remaining - required_credits
            if extra_credits > 0 and ctx.deps.skill_benchmark:
                elective_query = ctx.deps.skill_benchmark[0]
                catalog = chroma_query(elective_query, "courses", k=15)
                existing_ids = {c["course_id"] for c in remaining} | completed_ids
                for course in catalog:
                    cid = course.get("course_id", "")
                    cr = float(course.get("credits", 3))
                    if cid and cid not in existing_ids and cr <= extra_credits:
                        remaining.append({
                            "course_id": cid,
                            "title": course.get("title", ""),
                            "category": "Elective",
                            "credits": cr,
                            "relevance_reason": (
                                f"Elective aligned with skill gap: {elective_query}"
                            ),
                            "skills_covered": course.get("skills_taught", []),
                            "schedule": course.get(
                                "schedule", "See course catalog for schedule"
                            ),
                        })
                        existing_ids.add(cid)
                        extra_credits -= cr

            print(f"\n[search_courses] {len(remaining)} courses returned")
            print(json.dumps(remaining[:3], indent=2, default=str), "...")
            return remaining

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
