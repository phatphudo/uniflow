from pydantic import BaseModel, Field


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
