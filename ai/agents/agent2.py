"""
Agent 2 — Course & Event Advisor
Phase 1: MOCK_ADVISOR_REPORT used for the skeleton demo.
Phase 4: call get_advisor().run(..., deps=deps) for real LLM + RAG + web search.

System prompt is loaded from ai/prompts/agent2_advisor.md for easy versioning.
Agent and tools are defined lazily so Phase 1 runs without API keys.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai.agents.deps import OrchestratorDeps
from ai.prompts import load_prompt
from config import settings
from schemas.agent2 import (
    AdvisorReport,
    CourseRecommendation,
    EventRecommendation,
    GapReport,
)

# Loaded from disk — edit ai/prompts/agent2_advisor.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent2_advisor")

_advisor = None


def get_advisor():
    """Return the PydanticAI Advisor agent, creating it on first call."""
    global _advisor
    if _advisor is None:
        import httpx
        from pydantic_ai import Agent, RunContext

        _advisor = Agent(
            model=settings.ai_model,
            output_type=AdvisorReport,
            deps_type=OrchestratorDeps,
            system_prompt=_SYSTEM_PROMPT,
        )

        @_advisor.tool
        async def search_courses(
            ctx: RunContext[OrchestratorDeps], query: str
        ) -> list[dict]:
            """Semantic search over the college course catalog in ChromaDB."""
            results = ctx.deps.course_collection.query(
                query_texts=[query],
                n_results=5,
            )
            return [
                {**meta, "similarity": dist}
                for meta, dist in zip(
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

        @_advisor.tool
        async def search_events(
            ctx: RunContext[OrchestratorDeps], query: str
        ) -> list[dict]:
            """Live web search for professional events via Serper API."""
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": ctx.deps.search_api_key},
                    json={"q": query, "num": 10},
                )
            return resp.json().get("organic", [])

    return _advisor


# ── Phase 1 mock ──────────────────────────────────────────────────────────────
MOCK_ADVISOR_REPORT = AdvisorReport(
    gap_report=GapReport(
        benchmark_score=62,
        matched_skills=["Agile/Scrum", "User Research"],
        missing_skills=["Product Roadmap", "Stakeholder Management"],
        top_gap="Product Roadmap",
        top_gap_evidence=(
            "Resume lists execution-level project work but lacks evidence of owning "
            "a multi-quarter roadmap or making build/buy/partner tradeoffs."
        ),
    ),
    course_recs=[
        CourseRecommendation(
            course_id="BUS-412",
            title="Product Strategy & Roadmapping",
            relevance_reason="Directly teaches roadmap frameworks used by PMs at tech companies.",
            skills_covered=["Product Roadmap", "Stakeholder Management", "OKRs"],
            schedule="TTh 2:00–3:30 PM | Spring semester",
            open_seats=8,
        ),
        CourseRecommendation(
            course_id="CS-305",
            title="Applied Data Analysis",
            relevance_reason="Covers SQL and A/B testing, both listed as nice-to-have for the role.",
            skills_covered=["SQL", "A/B Testing", "Data Analysis"],
            schedule="MWF 9:00–10:00 AM | Spring semester",
            open_seats=15,
        ),
    ],
    event_recs=[
        EventRecommendation(
            title="SF Product Managers Meetup — Feb 2026",
            organiser="ProductTank San Francisco",
            event_datetime=datetime(2026, 2, 27, 18, 30, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 2, 27, 21, 0, tzinfo=timezone.utc),
            location="Salesforce Tower, San Francisco, CA",
            url="https://www.meetup.com/producttank-sf/",  # type: ignore[arg-type]
            relevance_reason="Monthly PM community meetup with lightning talks and open networking.",
            event_type="networking",
        ),
        EventRecommendation(
            title="Mind the Product — Product Leadership Workshop",
            organiser="Mind the Product",
            event_datetime=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 3, 10, 17, 0, tzinfo=timezone.utc),
            location="Online",
            url="https://www.mindtheproduct.com/",  # type: ignore[arg-type]
            relevance_reason="Full-day workshop on roadmap strategy and stakeholder communication.",
            event_type="workshop",
        ),
    ],
    calendar_push_ready=True,
)
