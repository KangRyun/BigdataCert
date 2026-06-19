"""사용자 본인 데이터 조회 API.

- GET /me/submissions  최근 제출 이력
- GET /me/progress     문제 유형별 시도/통과/해결 통계
"""

from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.content_loader import repository as content_repo
from app.db import get_session
from app.db.models import Submission, User
from app.deps import get_current_user

router = APIRouter(prefix="/me", tags=["me"])


class SubmissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: str
    passed: bool
    score: float
    metric_name: str
    feedback: str
    error_code: str | None
    created_at: datetime


class TypeProgress(BaseModel):
    attempts: int
    passed_attempts: int
    solved: int


class ProgressResponse(BaseModel):
    practical_1: TypeProgress
    practical_2: TypeProgress
    practical_3: TypeProgress
    written: TypeProgress


def _zero() -> TypeProgress:
    return TypeProgress(attempts=0, passed_attempts=0, solved=0)


@router.get("/submissions", response_model=list[SubmissionPublic])
def my_submissions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    problem_id: str | None = Query(default=None),
) -> list[Submission]:
    q = db.query(Submission).filter_by(user_id=user.id)
    if problem_id:
        q = q.filter_by(problem_id=problem_id)
    return q.order_by(desc(Submission.created_at)).limit(limit).all()


@router.get("/progress", response_model=ProgressResponse)
def my_progress(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> ProgressResponse:
    rows = db.query(Submission).filter_by(user_id=user.id).all()

    stats: dict[str, dict] = defaultdict(
        lambda: {"attempts": 0, "passed_attempts": 0, "solved_problems": set()}
    )
    for s in rows:
        problem = content_repo.get(s.problem_id)
        if not problem:
            continue
        bucket = stats[problem.exam_type]
        bucket["attempts"] += 1
        if s.passed:
            bucket["passed_attempts"] += 1
            bucket["solved_problems"].add(s.problem_id)

    def to_progress(et: str) -> TypeProgress:
        b = stats.get(et)
        if not b:
            return _zero()
        return TypeProgress(
            attempts=b["attempts"],
            passed_attempts=b["passed_attempts"],
            solved=len(b["solved_problems"]),
        )

    return ProgressResponse(
        practical_1=to_progress("practical_1"),
        practical_2=to_progress("practical_2"),
        practical_3=to_progress("practical_3"),
        written=to_progress("written"),
    )
