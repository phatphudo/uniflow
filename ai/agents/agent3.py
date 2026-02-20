"""
Agent 3 — Interview Coach
Phase 1: MOCK_INTERVIEW_RESULT used for the skeleton demo.
Phase 5: call get_interview_coach().run(prompt) for real STAR evaluation.

System prompt is loaded from ai/prompts/agent3_interview_coach.md for easy versioning.
Agent is created lazily so Phase 1 works without API keys.
"""

from __future__ import annotations

from ai.prompts import load_prompt
from schemas.agent3 import InterviewResult, StarScores

# Loaded from disk — edit ai/prompts/agent3_interview_coach.md to tune the prompt.
_SYSTEM_PROMPT = load_prompt("agent3_interview_coach")

_interview_coach = None


def get_interview_coach():
    """Return the PydanticAI Interview Coach agent, creating it on first call."""
    global _interview_coach
    if _interview_coach is None:
        from pydantic_ai import Agent

        _interview_coach = Agent(
            model="google-gla:gemini-1.5-pro",
            result_type=InterviewResult,
            system_prompt=_SYSTEM_PROMPT,
        )
    return _interview_coach


# ── Phase 1 mock ──────────────────────────────────────────────────────────────
MOCK_INTERVIEW_RESULT = InterviewResult(
    question=(
        "Describe a time you took ownership of defining the roadmap for a product area — "
        "how did you decide what to build, align stakeholders with competing priorities, "
        "and measure success after launch?"
    ),
    student_answer=(
        "In my internship I helped the team decide which features to ship for Q3. "
        "I talked to a few users and wrote up my recommendations. The team liked them "
        "and we shipped on time."
    ),
    star_scores=StarScores(situation=14, task=10, action=12, result=8),
    strengths=[
        "Demonstrated initiative in collecting user feedback.",
        "Clear outcome mentioned — shipped on time.",
    ],
    improvements=[
        "Situation lacked specificity — what was the product, team size, constraints?",
        "Task was vague — what exactly was your role vs the team's?",
        "Actions need more concrete detail — which frameworks or methods did you use?",
        "Result had no measurable impact — revenue, retention, NPS?",
    ],
    stronger_closing=(
        "A stronger close: 'The feature shipped in Q3 and drove a 12% increase in DAU "
        "within 30 days. I presented the results to the VP, which led to the team "
        "doubling down on the initiative in Q4.'"
    ),
)
