---
name: bigdata-prep-orchestrator
description: "빅데이터분석기사 실기 연습 웹사이트의 모든 빌드·확장·운영 작업을 총괄하는 오케스트레이터. 풀빌드(초기 구축), 화면 추가, 백엔드 엔드포인트 추가, 문제 콘텐츠 제작·확장, 채점기 수정, Docker·CI 작업, 통합 검증, 오답·진도·인증 기능 추가 등 모든 도메인 작업에 사용. 트리거 — '빅분기 사이트', '빅분기 웹', '문제 만들기', '문제 추가', '문제 풀이 페이지', '코드 에디터', '채점기', '오답노트', '진도 대시보드', '회원가입', '풀스택 빌드', 'Docker 묶기', 'CI 파이프라인'. 후속 작업 — 'X만 다시', '이전 결과 기반', '다시 실행', '재실행', '업데이트', '수정', '보완', '결과 개선'도 모두 이 스킬."
---

# 빅분기 실기 연습 사이트 오케스트레이터

빅데이터분석기사 실기 연습 웹사이트의 모든 작업을 5명의 전문 에이전트 팀(content-author, backend-engineer, frontend-engineer, infra-engineer, qa-integration)으로 조율한다.

## 실행 모드: 에이전트 팀 (감독자 + 팬아웃/팬인 + 생성-검증 복합)

풀빌드는 팀 모드 필수 — 백엔드/프론트의 API 계약, 콘텐츠↔채점기의 정답 계약, QA의 경계면 검증이 실시간으로 맞물려야 한다. 단일 작업(예: "문제 5개만 추가")은 동일한 팀 구성으로 가되 작업 할당이 1명에 집중된다.

## 에이전트 구성

| 팀원 | 에이전트 타입 | 역할 | 주 스킬 | 출력 위치 |
|------|-------------|------|---------|----------|
| content-author | content-author (커스텀) | 빅분기 문제·해설·정답코드 | bigdata-content-creation | `content/`, `_workspace/{phase}_content_*.json` |
| backend-engineer | backend-engineer (커스텀) | FastAPI + 샌드박스 + 채점 + DB | python-sandbox-execution | `backend/`, `_workspace/{phase}_backend_*.md`, `_workspace/openapi.json` |
| frontend-engineer | frontend-engineer (커스텀) | Next.js UI + Monaco + 훅 | nextjs-codingpad-patterns | `frontend/`, `_workspace/{phase}_frontend_*.md` |
| infra-engineer | infra-engineer (커스텀) | Docker + CI + 환경 | (인라인) | `Dockerfile*`, `docker-compose*.yml`, `.github/workflows/`, `_workspace/{phase}_infra_*.md` |
| qa-integration | qa-integration (커스텀) | 경계면 정합성 + E2E | (인라인) | `tests/integration/`, `tests/e2e/`, `_workspace/{phase}_qa_report.md` |

## 워크플로우

### Phase 0: 컨텍스트 확인 (필수)

작업 시작 전 기존 산출물을 확인하여 실행 모드를 결정한다.

1. `/home/kr9370/빅분기/_workspace/` 디렉토리 존재 여부 확인
2. 프로젝트 루트의 `backend/`, `frontend/`, `content/` 디렉토리 존재 여부 확인
3. 실행 모드 결정:
   - **모두 미존재** → **초기 풀빌드**. Phase 1~5 전체 실행
   - **`_workspace/` 존재 + 사용자가 부분 작업 요청** (예: "문제 5개 추가", "오답노트 화면만") → **부분 재실행**. 해당 에이전트에 직접 작업 할당, 나머지 에이전트는 옵저버
   - **`_workspace/` 존재 + 사용자가 새 풀빌드 요청** → 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 풀빌드
4. 부분 재실행 시: 이전 산출물 경로를 해당 에이전트의 프롬프트에 포함

### Phase 1: 요구사항 분석 및 작업공간 준비

1. 사용자 입력 분석:
   - 작업 유형: 풀빌드 / 화면 추가 / 콘텐츠 추가 / 채점기 수정 / Docker 묶기 / E2E 검증 / 기타
   - 영향 범위: 어느 에이전트가 주도하는가, 어느 에이전트가 협업하는가
2. `_workspace/` 생성 (Phase 0 결과에 따라)
3. 사용자에게 작업 계획 요약 보고 → 승인 후 진행

**작업 유형별 기본 할당:**

| 작업 유형 | 주도 | 협업 | QA 트리거 |
|----------|------|------|----------|
| 풀빌드 (전체 구축) | 전원 | 전원 | 매 모듈 완성 시 incremental |
| 화면 추가 | frontend-engineer | backend-engineer(API 추가시) | shape 검증 |
| 백엔드 엔드포인트 추가 | backend-engineer | frontend-engineer(훅 추가) | OpenAPI 변경 검증 |
| 문제 콘텐츠 추가 | content-author | backend-engineer(채점기 확장시) | solution_code 회귀 |
| 채점기 수정 | backend-engineer | content-author | 전 문제 재채점 |
| Docker 묶기 | infra-engineer | backend/frontend | docker-compose E2E |
| 회원·진도·오답노트 | backend-engineer + frontend-engineer | content-author(데이터 모델 영향시) | 인증 플로우 E2E |

### Phase 2: 팀 구성

```
TeamCreate(
  team_name: "bigdata-prep-team",
  members: [
    {
      name: "content-author",
      agent_type: "content-author",
      model: "opus",
      prompt: "당신은 빅분기 콘텐츠 작가입니다. .claude/agents/content-author.md를 따르고, bigdata-content-creation 스킬을 사용합니다. 작업 디렉토리: /home/kr9370/빅분기. 이번 Phase의 책임: {작업유형별 책임 명시}"
    },
    {
      name: "backend-engineer",
      agent_type: "backend-engineer",
      model: "opus",
      prompt: "당신은 백엔드 엔지니어입니다. .claude/agents/backend-engineer.md를 따르고, python-sandbox-execution 스킬을 사용합니다. 작업 디렉토리: /home/kr9370/빅분기. 이번 Phase의 책임: {...}"
    },
    {
      name: "frontend-engineer",
      agent_type: "frontend-engineer",
      model: "opus",
      prompt: "당신은 프론트엔드 엔지니어입니다. .claude/agents/frontend-engineer.md를 따르고, nextjs-codingpad-patterns 스킬을 사용합니다. 작업 디렉토리: /home/kr9370/빅분기. 이번 Phase의 책임: {...}"
    },
    {
      name: "infra-engineer",
      agent_type: "infra-engineer",
      model: "opus",
      prompt: "당신은 인프라 엔지니어입니다. .claude/agents/infra-engineer.md를 따릅니다. 작업 디렉토리: /home/kr9370/빅분기. 이번 Phase의 책임: {...}"
    },
    {
      name: "qa-integration",
      agent_type: "qa-integration",
      model: "opus",
      prompt: "당신은 통합 QA입니다. .claude/agents/qa-integration.md를 따릅니다. 작업 디렉토리: /home/kr9370/빅분기. 이번 Phase의 책임: 모듈 완성 알림 수신 시 즉시 해당 경계면을 검증."
    }
  ]
)
```

> 부분 재실행에서 한두 명만 필요해도 5명 모두 팀에 두되, 작업이 없는 에이전트는 옵저버로 둔다 — 후속 변경이 다른 에이전트에 파급될 수 있어 즉시 통신할 수 있어야 한다.

### Phase 3: 작업 등록 + 자체 조율 실행

**3-1. 작업 등록 (풀빌드 기준 — 부분 작업은 해당 영역만):**

```
TaskCreate(tasks: [
  // 콘텐츠
  { title: "작업형1 문제 5개 작성", assignee: "content-author" },
  { title: "작업형2 문제 3개 작성", assignee: "content-author" },
  { title: "작업형3 문제 3개 작성", assignee: "content-author" },
  { title: "필기 문제 10개 작성", assignee: "content-author" },

  // 백엔드
  { title: "FastAPI 프로젝트 부트스트랩", assignee: "backend-engineer" },
  { title: "DB 모델 (User/Problem/Submission/Note)", assignee: "backend-engineer" },
  { title: "샌드박스 + 채점기 (4가지 format)", assignee: "backend-engineer" },
  { title: "API 라우터 + OpenAPI 스냅샷", assignee: "backend-engineer" },
  { title: "JWT 인증", assignee: "backend-engineer" },

  // 프론트
  { title: "Next.js 부트스트랩 + shadcn 설치", assignee: "frontend-engineer" },
  { title: "라우팅 + 레이아웃", assignee: "frontend-engineer" },
  { title: "문제 목록·풀이 화면 + Monaco", assignee: "frontend-engineer", depends_on: ["API 라우터 + OpenAPI 스냅샷"] },
  { title: "대시보드 + 오답노트", assignee: "frontend-engineer", depends_on: ["JWT 인증"] },

  // 인프라
  { title: "로컬 개발 docker-compose", assignee: "infra-engineer" },
  { title: ".env.example + Makefile", assignee: "infra-engineer" },
  // (배포는 사용자 명시 후 진입)

  // QA (incremental)
  { title: "채점 회귀 (solution_code 일괄)", assignee: "qa-integration", depends_on: ["샌드박스 + 채점기 (4가지 format)", "작업형1 문제 5개 작성"] },
  { title: "API↔훅 shape 검증", assignee: "qa-integration", depends_on: ["API 라우터 + OpenAPI 스냅샷", "문제 목록·풀이 화면 + Monaco"] },
  { title: "E2E (docker-compose 전체 플로우)", assignee: "qa-integration", depends_on: ["로컬 개발 docker-compose"] }
])
```

> 팀원당 5~6개 작업 적정. 의존성은 `depends_on`으로 표현하여 자동 직렬화.

**3-2. 자체 조율 실행:**

팀원들은 공유 작업 목록에서 작업을 claim하여 수행한다. 리더(오케스트레이터)는 모니터링.

**팀원 간 통신 규칙:**

- **content-author ↔ backend-engineer**: expected_output 스키마는 양측 합의 사항. 변경 시 SendMessage로 즉시 통보. content-author가 신규 문제 작성 시 baseline 점수를 backend에 통보 (채점기가 사용)
- **backend-engineer ↔ frontend-engineer**: OpenAPI 스냅샷이 갱신될 때마다 backend가 frontend에게 SendMessage("openapi.json 갱신: {경로}, breaking change: yes/no, 변경: ..."). frontend는 즉시 `pnpm types:gen` 수행
- **backend/frontend ↔ infra-engineer**: 런타임·빌드 요구사항 변경 시 SendMessage
- **모든 모듈 완성 시 → qa-integration**: 완성한 에이전트가 `SendMessage(to: "qa-integration", "모듈 X 완성, 경계면 검증 요청")`. QA는 즉시 검증 시작
- **QA 실패 → 책임 에이전트**: QA는 `SendMessage`로 재현 정보 전달. 책임 에이전트는 우선 수정. 양측 책임이면 양쪽 모두에게 발송하고 합의 요청

**리더 모니터링:**
- 유휴 알림 수신 시 TaskGet으로 전체 상태 확인
- 막힌 팀원에게 직접 SendMessage 또는 작업 재할당
- QA 보고서 도착 시 사용자에게 중간 요약 보고

### Phase 4: 통합 + 최종 검증

1. 모든 작업 완료 대기 (TaskGet polling)
2. qa-integration의 최종 보고서(`_workspace/{phase}_qa_report.md`) Read
3. 실패 항목이 있으면:
   - 사소(개별 문제 1~2개 실패): 책임 에이전트에 즉시 수정 요청 후 재검증
   - 중대(채점 계약 깨짐, API shape 광범위 불일치): 사용자에게 보고하고 수정 진행 여부 합의
4. 통합 정합성 통과 시 다음 단계로

### Phase 5: 정리 + 사용자 보고

1. 팀원들에게 종료 요청 (SendMessage)
2. `TeamDelete`로 팀 정리
3. `_workspace/`는 보존 (사후 검증·감사용)
4. CLAUDE.md 변경 이력 테이블에 이번 작업 항목 추가
5. 사용자에게 최종 보고:
   - 생성·수정된 파일 요약
   - QA 통과/실패 요약
   - 다음 단계 제안 (예: "지금 단계는 로컬 동작 확인 가능. 배포 단계로 진입할까요?")
6. 피드백 요청 — "결과에서 개선할 부분이 있나요?"

## 데이터 흐름

```
                              [리더(오케스트레이터)]
                                       │
                                  TeamCreate
                                       │
       ┌───────────────┬───────────────┼───────────────┬───────────────┐
       ▼               ▼               ▼               ▼               ▼
  content-author  backend-engineer  frontend-engineer  infra-engineer  qa-integration
       │               │               │                       │               │
       │   ←──── expected_output 스키마 합의 ────→               │               │
       │               │               │                       │               │
       │           openapi.json ────────→ types:gen             │               │
       │               │               │                       │               │
       └────── solution_code ──→ 채점 회귀 ───────────────────────────────────────→
                       │               │                       │               │
                       └─── 런타임 요구사항 ─→                  │               │
                                       │               docker-compose ────→ E2E
                                       │                       │               │
                                       └─── 화면 마크업 합의 ────────────────────→
                                                                               │
                                                                               ▼
                                                                    _workspace/qa_report.md
                                                                               │
                                                                               ▼
                                                                    [리더: 통합 + 사용자 보고]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 팀원 1명 실패/중지 | 리더가 유휴 알림으로 감지 → 상태 확인 → 1회 재시작. 재실패 시 사용자에게 보고하고 누락 처리 |
| 채점 계약 불일치 (content vs backend) | 즉시 양측 합의 요청. 합의까지 해당 문제는 비활성 (배포 차단) |
| OpenAPI breaking change | frontend의 types:gen 실패 → 즉시 backend에게 SendMessage, 임시 any 사용 금지 |
| 샌드박스 탈출 의심 | backend가 즉시 인프라에 알림. 해당 PR/커밋 격리 |
| 타임아웃 (개별 작업) | 분할 재할당 (예: 문제 20개 작성 → 5개씩 4번) |
| 부분 결과로 진행해야 하는 경우 | 보고서에 "X 영역 누락" 명시. 사용자 승인 후 사용 |
| 의견 충돌 (예: 화면 레이아웃) | 양측 안을 _workspace/에 보관, 사용자에게 결정 요청 |

## 테스트 시나리오

### 정상 흐름 (초기 풀빌드)

1. 사용자: "빅분기 사이트 풀빌드 시작해줘"
2. Phase 0: `_workspace/`, `backend/`, `frontend/`, `content/` 모두 미존재 → 초기 풀빌드
3. Phase 1: 작업 계획 보고. 사용자 승인
4. Phase 2: 5명 팀 구성
5. Phase 3: 18개 작업 등록. 의존성에 따라 직렬·병렬 진행
   - 초기 병렬: content-author(문제 작성), backend-engineer(부트스트랩+샌드박스), frontend-engineer(부트스트랩), infra-engineer(docker-compose)
   - 의존 진행: backend의 OpenAPI 완성 → frontend의 훅·화면, content의 정답코드 → QA 회귀
6. Phase 4: QA 최종 보고서 모두 통과
7. Phase 5: 팀 정리. CLAUDE.md 갱신. 사용자에게 "로컬 동작 가능, `make dev` 또는 `docker-compose up` 안내" 보고
8. 예상 결과: `backend/`, `frontend/`, `content/`, `docker-compose.yml`, 21개 작업물 + QA 통과 보고서

### 부분 재실행 (문제 5개 추가)

1. 사용자: "작업형2 분류 문제 5개 더 추가해줘"
2. Phase 0: `_workspace/` 존재 + 부분 작업 → 부분 재실행
3. Phase 1: content-author 단독 작업, qa-integration 회귀 트리거. backend/frontend/infra는 옵저버
4. Phase 2: 팀 구성 (5명 그대로, content-author에 작업 집중)
5. Phase 3: 2개 작업 등록 — "분류 문제 5개 작성", "신규 문제 채점 회귀"
6. Phase 4: QA가 5개 모두 solution_code 통과 확인
7. Phase 5: `content/problems/practical_2/` 5개 추가, CLAUDE.md 변경 이력 업데이트
8. 예상 결과: 새 문제 5개 + QA 통과

### 에러 흐름 (채점 회귀 실패)

1. Phase 3 진행 중 QA가 SendMessage: "type2-classification-007 의 solution_code 실행 결과는 ROC-AUC 0.78인데 baseline 0.85 미달"
2. 리더가 보고 받고 content-author에게 SendMessage: "해당 문제의 solution_code 재검토 필요"
3. content-author가 코드 수정 (예: feature engineering 강화) → backend의 샌드박스로 재실행 요청
4. 재검증 통과 시 작업 재개. 2회 실패 시 사용자에게 보고 후 해당 문제 일시 비활성

## description 후속 작업 키워드 — 누락 방지

본 스킬 description은 다음 후속 키워드를 모두 포함하므로 다음 세션에서도 트리거된다:
- "X만 다시", "이전 결과 기반", "다시 실행", "재실행", "업데이트", "수정", "보완", "결과 개선"
- "문제 추가", "채점기 수정", "오답노트", "진도", "회원가입", "Docker 묶기"

신규 도메인 작업이 등장하면 description에 키워드를 추가하고 변경 이력에 기록한다.
