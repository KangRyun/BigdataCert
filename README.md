# 빅데이터분석기사 실기 연습

빅데이터분석기사 실기·필기 학습을 위한 풀스택 웹사이트.

## 스택

- **프론트엔드**: Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
- **백엔드**: FastAPI + SQLAlchemy 2.0
- **코드 실행**: Python 샌드박스 (subprocess + 향후 Docker 격리)
- **인증/회원**: JWT 기반
- **인프라**: 로컬은 Make/uvicorn/pnpm → 추후 docker-compose

## 콘텐츠 범위

- 작업형 1 — pandas·numpy 데이터 전처리/요약
- 작업형 2 — scikit-learn 분류/회귀 모델링
- 작업형 3 — scipy/statsmodels 통계 분석
- 필기 — 4과목 객관식 이론

## 디렉토리 (계획)

```
.
├── backend/        FastAPI 서버
├── frontend/       Next.js 클라이언트
├── content/        문제·해설 JSON + 샘플 데이터
├── tests/          통합·E2E 테스트
└── .claude/        하네스 (에이전트 5 + 스킬 4)
```

## 개발

초기 구축 진행 중. 빌드 단계는 `.claude/skills/bigdata-prep-orchestrator/SKILL.md`의 워크플로우를 따른다.
