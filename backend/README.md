# Backend — FastAPI

빅분기 실기 연습 사이트의 백엔드 서버.

## 설치 & 실행

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

확인:
- 서버: http://localhost:8000
- 헬스: http://localhost:8000/healthz
- 문서: http://localhost:8000/docs (OpenAPI Swagger UI)
- 샘플 문제: http://localhost:8000/problems/pp1-missing-001

## 환경변수

`.env.example` 참고. `CONTENT_DIR`는 문제 JSON이 저장된 경로 (기본: `../content`).

## 테스트

```bash
pytest -q
```

## OpenAPI 스냅샷 추출

프론트엔드의 타입 동기화용:

```bash
python -m app.openapi_dump > ../_workspace/openapi.json
```
