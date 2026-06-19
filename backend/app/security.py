"""비밀번호 해시 + JWT 발급/검증.

bcrypt 의 72바이트 자동 절단 이슈 → 패스워드는 schema 에서 길이 제한 (≤72).
JWT 는 HS256, 페이로드 sub=user_id(str), exp=만료시각.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str | None) -> bool:
    """OAuth-only 사용자는 password_hash 가 NULL → 항상 False."""
    if not hashed:
        return False
    try:
        return _pwd_ctx.verify(plain, hashed)
    except ValueError:
        return False


def create_access_token(subject: str, expires_days: int | None = None) -> str:
    exp = datetime.now(UTC) + timedelta(days=expires_days or settings.jwt_expires_days)
    payload = {"sub": subject, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    """유효한 토큰이면 sub(user_id 문자열), 아니면 None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    sub = payload.get("sub")
    return str(sub) if sub is not None else None
