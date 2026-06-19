"""FastAPI 진입점."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth as auth_api
from app.api import me as me_api
from app.api import problems as problems_api
from app.api import submissions as submissions_api
from app.config import settings
from app.content_loader import repository
from app.db import init_db

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    repository.load()
    yield


app = FastAPI(
    title="빅분기 실기 연습 API",
    version=__version__,
    description="빅데이터분석기사 실기 학습 사이트의 백엔드 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


app.include_router(auth_api.router)
app.include_router(problems_api.router)
app.include_router(submissions_api.router)
app.include_router(me_api.router)
