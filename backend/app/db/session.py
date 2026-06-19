"""DB 엔진과 세션 팩토리.

배포 단계에서는 Alembic 으로 마이그레이션 관리. MVP 는 create_all 로 간소화.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, connect_args=_connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """모델을 등록한 뒤 create_all. lifespan 에서 호출."""
    from app.db import models  # noqa: F401 — 모델 임포트로 metadata 등록

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
