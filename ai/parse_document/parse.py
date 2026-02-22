"""
ai/parse_document/parse.py — PDF parsing via LLM.

Two functions, one per document type:
  - parse_resume(file)     → str
  - parse_transcript(file) → TranscriptData

Both accept a Streamlit UploadedFile object, a file path string, or a Path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from pydantic_ai import Agent, BinaryContent

from config import settings
from schemas.inputs import ResumeData, TranscriptData

_resume_agent = None
_transcript_agent = None


def _read_bytes(file: Union[str, Path, object]) -> bytes:
    if hasattr(file, "seek"):
        file.seek(0)
        return file.read()
    return Path(file).expanduser().resolve().read_bytes()


def parse_resume(file: Union[str, Path, object]) -> ResumeData:
    """Extract structured resume data from a resume PDF.

    Returns a ResumeData object with name, skills, experience, education, and certifications.
    """
    global _resume_agent
    if _resume_agent is None:
        _resume_agent = Agent(model=settings.ai_model, output_type=ResumeData)

    pdf_bytes = _read_bytes(file)
    result = _resume_agent.run_sync(
        [
            (
                "Extract the candidate's information from this resume. "
                "Include full name, all skills, work experience with highlights, "
                "education, and certifications."
            ),
            BinaryContent(data=pdf_bytes, media_type="application/pdf"),
        ]
    )
    return result.output


def parse_transcript(file: Union[str, Path, object]) -> TranscriptData:
    """Extract structured transcript data from a transcript PDF.

    Returns a TranscriptData object with student name, GPA, and course lists.
    """
    global _transcript_agent
    if _transcript_agent is None:
        _transcript_agent = Agent(
            model=settings.ai_model,
            output_type=TranscriptData,
        )

    pdf_bytes = _read_bytes(file)
    result = _transcript_agent.run_sync(
        [
            (
                "Extract the student transcript data from this document. "
                "Return the student's full name, GPA, and all courses. "
                "For each course include: course_id, title, grade, credits, and semester. "
                "Separate completed courses from in-progress ones."
            ),
            BinaryContent(data=pdf_bytes, media_type="application/pdf"),
        ]
    )
    return result.output
