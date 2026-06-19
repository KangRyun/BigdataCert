"""제출·채점 API.

POST /submissions
- 요청: problem_id, code
- 응답: GradingResult { passed, score, metric_name, feedback, error_code? }
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.content_loader import repository
from app.grading import GradingResult, grade
from app.sandbox import run_in_sandbox

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionRequest(BaseModel):
    problem_id: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., max_length=100_000)


@router.post("", response_model=GradingResult)
def submit_code(payload: SubmissionRequest) -> GradingResult:
    problem = repository.get(payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail={"error_code": "PROBLEM_NOT_FOUND"})

    sample_paths = repository.sample_data_paths(payload.problem_id)
    truth_paths = repository.truth_data_paths(payload.problem_id)
    sandbox_result = run_in_sandbox(payload.code, sample_data_paths=sample_paths)
    return grade(problem.expected_output, sandbox_result, truth_paths=truth_paths)
