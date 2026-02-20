from datetime import datetime

from pydantic import BaseModel, HttpUrl


class CourseRecommendation(BaseModel):
    course_id: str
    title: str
    relevance_reason: str
    skills_covered: list[str]
    schedule: str
    open_seats: int | None = None


class EventRecommendation(BaseModel):
    title: str
    organiser: str
    event_datetime: datetime
    end_datetime: datetime
    location: str  # address or "Online"
    url: HttpUrl
    relevance_reason: str
    event_type: str  # "networking" | "workshop" | "conference" | "career_fair"


class GapReport(BaseModel):
    benchmark_score: int  # 0–100
    matched_skills: list[str]
    missing_skills: list[str]
    top_gap: str
    top_gap_evidence: str


class AdvisorReport(BaseModel):
    gap_report: GapReport
    course_recs: list[CourseRecommendation]  # 2–3 courses from RAG
    event_recs: list[EventRecommendation]  # 2–3 events from web search
    calendar_push_ready: bool = True
