from datetime import datetime

from pydantic import BaseModel, HttpUrl


class CourseRecommendation(BaseModel):
    course_id: str
    title: str
    category: str        # degree requirement category this course satisfies
    credits: float
    relevance_reason: str
    skills_covered: list[str]
    schedule: str
    open_seats: int | None = None


class SemesterPlan(BaseModel):
    semester_label: str          # "Semester 1", "Semester 2", …, "Final Semester"
    courses: list[CourseRecommendation]
    total_credits: float
    is_final: bool = False


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
    strength: str
    weakness: str
    tips_for_enhance: str


class AdvisorReport(BaseModel):
    gap_report: GapReport
    study_plan: list[SemesterPlan]   # semester-organised course roadmap
    event_recs: list[EventRecommendation]  # 2–3 events from web search
    calendar_push_ready: bool = True
