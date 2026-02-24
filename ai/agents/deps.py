from dataclasses import dataclass, field

from schemas.inputs import TranscriptData

# googleapiclient.discovery.Resource is injected at runtime.
# Typed as `object` here to avoid heavy import overhead at module load.


@dataclass
class OrchestratorDeps:
    resume_text: str
    transcript_data: TranscriptData
    calendar_service: object | None  # google API Resource, or None if not configured
    search_api_key: str = field(default="")
    program_enrolled: str = field(default="")
    credits_remaining: int = field(default=0)
    skill_benchmark: list[str] = field(default_factory=list)
