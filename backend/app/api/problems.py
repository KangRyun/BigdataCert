"""문제 조회 API.

- GET /problems — 목록 (필터: exam_type, difficulty)
- GET /problems/{id} — 상세 (정답·해설 제외)
"""

from fastapi import APIRouter, HTTPException, Query

from app.content_loader import repository
from app.schemas.problem import Difficulty, ExamType, ProblemDetail, ProblemSummary

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemSummary])
def list_problems(
    exam_type: ExamType | None = Query(default=None),
    difficulty: Difficulty | None = Query(default=None),
) -> list[ProblemSummary]:
    items = list(repository.all())
    if exam_type:
        items = [p for p in items if p.exam_type == exam_type]
    if difficulty:
        items = [p for p in items if p.difficulty == difficulty]
    items.sort(key=lambda p: p.problem_id)
    return [ProblemSummary.model_validate(p.model_dump()) for p in items]


@router.get("/{problem_id}", response_model=ProblemDetail)
def get_problem(problem_id: str) -> ProblemDetail:
    problem = repository.get(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail={"error_code": "PROBLEM_NOT_FOUND"})
    return ProblemDetail.model_validate(problem.model_dump())
