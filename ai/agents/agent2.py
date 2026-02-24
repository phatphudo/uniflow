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
from retrieval.src.vector_store import query as chroma_query
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

        @_advisor.tool_plain
        def search_courses(query: str) -> list[dict]:
            """Semantic search over the college course catalog in ChromaDB."""
            results = chroma_query(query, k=5)
            import json

            print(f"\n[search_courses] query={query!r}")
            print(f"[search_courses] results ({len(results)}):")
            print(json.dumps(results, indent=2, default=str))
            return results

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
