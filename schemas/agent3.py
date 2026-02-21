from pydantic import BaseModel, Field


class StarScores(BaseModel):
    situation: int = Field(..., ge=0, le=25)
    task: int = Field(..., ge=0, le=25)
    action: int = Field(..., ge=0, le=25)
    result: int = Field(..., ge=0, le=25)

    @property
    def total(self) -> int:
        return self.situation + self.task + self.action + self.result


class InterviewResult(BaseModel):
    question: str
    student_answer: str
    star_scores: StarScores
    strengths: list[str]
    improvements: list[str]
    stronger_closing: str

    @property
    def result(self):
        return {
            "star_scores.total": self.star_scores.total,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "stronger_closing": self.stronger_closing,
        }

class Agent3Input(BaseModel):
    student_answer: str
    