.PHONY: help install backend frontend test openapi clean

help:
	@echo "사용 가능한 타겟:"
	@echo "  make install         - 백엔드 venv 생성 + 의존성 설치 (Python 3.11+)"
	@echo "  make backend         - 백엔드 dev 서버 (uvicorn :8000)"
	@echo "  make frontend        - 프론트 dev 서버 (Next.js :3000, node 필요)"
	@echo "  make test            - 백엔드 pytest"
	@echo "  make openapi         - OpenAPI 스냅샷을 _workspace/openapi.json 으로 추출"
	@echo "  make clean           - venv, .next, node_modules 정리"

install:
	cd backend && python3 -m venv .venv && \
		.venv/bin/pip install --upgrade pip && \
		.venv/bin/pip install -e ".[dev]"

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm install && npm run dev

test:
	cd backend && .venv/bin/pytest -q

openapi:
	cd backend && .venv/bin/python -m app.openapi_dump > ../_workspace/openapi.json
	@echo "wrote _workspace/openapi.json"

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/**/__pycache__
	rm -rf frontend/.next frontend/node_modules
