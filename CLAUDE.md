# 빅데이터분석기사 실기 연습 웹사이트

## 하네스: 빅분기 실기 연습 사이트

**목표:** 빅데이터분석기사 실기·필기 학습자를 위한 풀스택 웹사이트(Next.js + FastAPI) 구축 및 운영. 브라우저 코드 에디터, 자동 채점, 단계별 힌트·해설, 진도·오답노트(회원) 기능 일체.

**트리거:** 빅분기/빅데이터분석기사 사이트 관련 모든 요청(문제 생성·추가·수정, 채점기 변경, 화면 추가, 백엔드 엔드포인트, Docker·CI 작업, 통합 검증, 회원 기능 등) 시 `bigdata-prep-orchestrator` 스킬을 사용하라. 단순 질문·맞춤법 정도는 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-19 | 초기 구성 | 전체 (에이전트 5 + 스킬 4) | 풀스택 빌드 + 콘텐츠 제작 + QA 통합을 위한 하네스 신규 구축 |
| 2026-06-19 | Phase 1 최소 수직 슬라이스 | backend/, frontend/, content/, Makefile | 백엔드 FastAPI 부트스트랩 + 샘플 문제 1개 + 프론트 Next.js 부트스트랩 (node 설치 전 소스만). pytest 4/4 통과, OpenAPI 스냅샷 생성 |
| 2026-06-19 | Phase 2 채점 슬라이스 | sandbox/, grading/, /submissions, Monaco UI | 사용자 코드 → 격리 실행 → scalar 채점 vertical 완성. pytest 27/27 통과, 라이브 3시나리오(정답/오답/금지패턴) 검증 |
| 2026-06-19 | Phase 3 채점기·콘텐츠 확장 | csv/dict/choice 그레이더, 작업형2/3/필기 문제, schema split | 전 format 지원. 작업형2(이탈 분류, ROC-AUC 0.86), 작업형3(t-검정 dict), 필기(객관식) 1개씩. 보안 수정: answer/baseline/solution_code 가 GET /problems/{id} 응답에 노출되던 누수 차단. pytest 41/41, 라이브 4-format E2E 통과 |
| 2026-06-19 | Auto-snapshot Stop hook | .claude/hooks/auto-snapshot.sh + settings.json | 응답 종료마다 변경분 자동 커밋. _workspace 등 .gitignore 자동 제외. push 없음 |
| 2026-06-19 | Phase 4a 회원 도메인 | db/, security, auth/me 라우터, 프론트 sign-in/up + /me | SQLAlchemy + JWT 인증, 제출 영속화, 진도 집계. pytest 59/59, 라이브 register→login→submit→/me 검증. bcrypt 4.x 호환 이슈로 bcrypt<4 핀 |
| 2026-06-19 | Phase 4b 오답노트 + 풀이 컨텍스트 | Note 모델, /me/notes CRUD, my-history + my-note 위젯, /me/notes 목록 | 회원 도메인 완결. 한 user×problem 당 노트 1개(upsert). 풀이 화면에서 제출 후 history 자동 갱신. pytest 73/73 |
