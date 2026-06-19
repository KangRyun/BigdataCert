from pydantic import BaseModel


class GradingResult(BaseModel):
    passed: bool
    score: float
    metric_name: str
    feedback: str
    error_code: str | None = None
