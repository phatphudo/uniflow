from dataclasses import dataclass, field

from schemas.inputs import TranscriptData

# chromadb.Collection and googleapiclient.discovery.Resource are injected at
# runtime. Typed as `object` here to avoid heavy import overhead at module load.


@dataclass
class OrchestratorDeps:
    resume_text: str
    transcript_data: TranscriptData
    course_collection: object  # chromadb.Collection
    calendar_service: object | None  # google API Resource, or None if not configured
    search_api_key: str = field(default="")
