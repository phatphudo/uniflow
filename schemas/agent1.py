from pydantic import BaseModel


class PositionProfile(BaseModel):
    required_skills: list[str]
    must_have: list[str]
    nice_to_have: list[str]
    seniority_indicators: list[str]
    industry_scope: str  # 2–3 sentence description
    interview_topics: list[str]
