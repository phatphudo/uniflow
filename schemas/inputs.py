from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    company: str
    role: str
    duration: str        # e.g. "Jun 2023 – Aug 2023"
    highlights: list[str]


class ResumeData(BaseModel):
    full_name: str
    skills: list[str]
    work_experience: list[WorkExperience] = []
    education: list[str] = []   # e.g. ["B.S. Computer Science, UCLA, 2024"]
    certifications: list[str] = []


class TranscriptCourse(BaseModel):
    course_id: str
    title: str
    grade: str  # e.g. "A", "B+", "P"
    credits: float
    semester: str  # e.g. "Fall 2023"


class TranscriptData(BaseModel):
    student_name: str
    gpa: float
    completed: list[TranscriptCourse]
    in_progress: list[TranscriptCourse] = []


class StudentInput(BaseModel):
    resume_text: str = Field(..., description="Raw text parsed from resume PDF")
    transcript_data: TranscriptData
    target_position: str = Field(
        ..., description="e.g. Product Manager at a tech startup"
    )
