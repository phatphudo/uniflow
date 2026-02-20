from pydantic import BaseModel

from .agent1 import PositionProfile
from .agent2 import AdvisorReport
from .agent3 import InterviewResult


class FinalReport(BaseModel):
    student_name: str
    target_position: str
    position_profile: PositionProfile
    advisor_report: AdvisorReport
    interview_result: InterviewResult
    calendar_synced: bool = False

    @property
    def benchmark_score(self) -> int:
        return self.advisor_report.gap_report.benchmark_score

    @property
    def interview_score(self) -> int:
        return self.interview_result.star_scores.total
