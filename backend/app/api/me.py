"""사용자 본인 데이터 조회 API.

- GET    /me/submissions       최근 제출 이력 (problem_id 필터링 가능)
- GET    /me/progress           문제 유형별 시도/통과/해결 통계
- GET    /me/notes              내 오답노트 전체
- GET    /me/notes/{problem_id} 단일 노트 조회 (없으면 404)
- PUT    /me/notes/{problem_id} 노트 upsert (있으면 update, 없으면 create)
- DELETE /me/notes/{problem_id} 노트 삭제 (idempotent)
"""

from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.content_loader import repository as content_repo
from app.db import get_session
from app.db.models import Note, Submission, User
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


# ---------- 오답노트 ----------


class NotePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: str
    content: str
    created_at: datetime
    updated_at: datetime


class NoteUpsert(BaseModel):
    content: str = Field(..., max_length=20_000)


@router.get("/notes", response_model=list[NotePublic])
def list_my_notes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> list[Note]:
    return (
        db.query(Note)
        .filter_by(user_id=user.id)
        .order_by(desc(Note.updated_at))
        .all()
    )


@router.get("/notes/{problem_id}", response_model=NotePublic)
def get_my_note(
    problem_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Note:
    note = db.query(Note).filter_by(user_id=user.id, problem_id=problem_id).first()
    if not note:
        raise HTTPException(status_code=404, detail={"error_code": "NOTE_NOT_FOUND"})
    return note


@router.put("/notes/{problem_id}", response_model=NotePublic)
def upsert_my_note(
    problem_id: str,
    payload: NoteUpsert,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Note:
    # 무관한 problem_id 로 노트가 만들어지지 않도록 검증
    if not content_repo.get(problem_id):
        raise HTTPException(status_code=404, detail={"error_code": "PROBLEM_NOT_FOUND"})

    note = db.query(Note).filter_by(user_id=user.id, problem_id=problem_id).first()
    if note:
        note.content = payload.content
    else:
        note = Note(user_id=user.id, problem_id=problem_id, content=payload.content)
        db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/notes/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_note(
    problem_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Response:
    note = db.query(Note).filter_by(user_id=user.id, problem_id=problem_id).first()
    if note:
        db.delete(note)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
