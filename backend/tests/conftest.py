"""테스트 전역 fixture.

- DATABASE_URL / JWT_SECRET 을 테스트 전용 값으로 강제 (app import 전에 설정)
- 세션 시작 시 테이블 새로 생성, 종료 시 drop
- 각 테스트 후 자동 truncate
"""

import os
import sys

# app 임포트 전에 env 강제 → engine 이 테스트 DB 로 바인딩됨
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_e2e.db")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")

import pytest  # noqa: E402

# 테스트 DB 정리 — pyc 캐시 영향 회피
if "app" in sys.modules:
    # 안전 차원의 가드. 일반적으로 불필요.
    pass

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
import app.db.models  # noqa: F401, E402  — register models


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _truncate_after_each_test():
    yield
    with SessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
