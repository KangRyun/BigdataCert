"""인증 의존성 (FastAPI Depends)."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_session
from app.db.models import User
from app.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User | None:
    if creds is None or not creds.credentials:
        return None
    sub = decode_token(creds.credentials)
    if not sub:
        return None
    try:
        user_id = int(sub)
    except ValueError:
        return None
    return db.get(User, user_id)


def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail={"error_code": "AUTH_REQUIRED"})
    return user
