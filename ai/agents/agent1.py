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
        )
    return _position_analyst


# ── Phase 1 mock: bypass real LLM call ───────────────────────────────────────
MOCK_POSITION_PROFILE = PositionProfile(
    required_skills=[
        "Product Roadmap",
        "Stakeholder Management",
        "Data Analysis",
        "Agile/Scrum",
        "User Research",
        "SQL",
        "A/B Testing",
    ],
    must_have=[
        "Product Roadmap",
        "Stakeholder Management",
        "Agile/Scrum",
        "User Research",
    ],
    nice_to_have=["SQL", "A/B Testing", "Data Analysis"],
    seniority_indicators=[
        "mid-level",
        "2-4 years experience",
        "cross-functional team lead",
    ],
    industry_scope=(
        "Product Managers at tech startups operate within fast-paced, cross-functional teams "
        "spanning engineering, design, and marketing. The role requires balancing short-term "
        "delivery with long-term product vision, often reporting directly to a VP of Product."
    ),
    interview_topics=[
        "Tell me about a product you built from 0 to 1",
        "How do you prioritize features with competing stakeholder demands?",
        "Describe a time you used data to change a product decision",
        "How do you define success for a product launch?",
        "Conflict resolution with engineers",
    ],
)
