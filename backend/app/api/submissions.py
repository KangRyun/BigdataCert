"""제출·채점 API.

POST /submissions
- 요청: problem_id, code
- 응답: GradingResult { passed, score, metric_name, feedback, error_code? }
- 로그인 사용자라면 결과를 DB에 기록 (Submission). 비로그인은 결과만 반환, 기록 X.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.content_loader import repository
from app.db import get_session
from app.db.models import Submission, User
from app.deps import get_current_user_optional
from app.grading import GradingResult, grade
from app.sandbox import run_in_sandbox

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionRequest(BaseModel):
    problem_id: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., max_length=100_000)


@router.post("", response_model=GradingResult)
def submit_code(
    payload: SubmissionRequest,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_session),
) -> GradingResult:
    problem = repository.get(payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail={"error_code": "PROBLEM_NOT_FOUND"})

    sample_paths = repository.sample_data_paths(payload.problem_id)
    truth_paths = repository.truth_data_paths(payload.problem_id)
    sandbox_result = run_in_sandbox(payload.code, sample_data_paths=sample_paths)
    result = grade(problem.expected_output, sandbox_result, truth_paths=truth_paths)

    if user is not None:
        record = Submission(
            user_id=user.id,
            problem_id=payload.problem_id,
            code=payload.code,
            passed=result.passed,
            score=result.score,
            metric_name=result.metric_name,
            feedback=result.feedback,
            error_code=result.error_code,
        )
        db.add(record)
        db.commit()

    return result
