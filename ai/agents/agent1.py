"""
Agent 1 — Position Analyst
Phase 1: MOCK_POSITION_PROFILE used for the skeleton demo.
Phase 2: call get_position_analyst().run(target_position) for real LLM output.

System prompt is loaded from ai/prompts/agent1_position_analyst.md for easy versioning.
The agent is created lazily so Phase 1 works without a GOOGLE_API_KEY set.
"""

from __future__ import annotations

from ai.prompts import load_prompt
from config import settings
from schemas.agent1 import PositionProfile

# Loaded from disk — edit ai/prompts/agent1_position_analyst.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent1_position_analyst")

# Lazy singleton — created only when get_position_analyst() is first called.
_position_analyst = None


def get_position_analyst():
    """Return the PydanticAI Position Analyst agent, creating it on first call."""
    global _position_analyst
    if _position_analyst is None:
        from pydantic_ai import Agent

        _position_analyst = Agent(
            model=settings.ai_model,
            output_type=PositionProfile,
            system_prompt=_SYSTEM_PROMPT,
            output_retries=3,
        )
    return _position_analyst


async def analyze_position(job_description: str):
    analyst = get_position_analyst()
    result = await analyst.run(job_description)
    return result.output  # returns a populated PositionProfile instance
