# Frontend — Next.js 15

빅분기 실기 연습 사이트의 사용자 인터페이스.

## 설치 & 실행

먼저 Node.js 20+ 가 필요합니다. nvm 사용 예:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20 && nvm use 20
```

설치 & 개발 서버:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

브라우저: http://localhost:3000

> 백엔드(`http://localhost:8000`)가 먼저 실행 중이어야 문제 목록·상세가 보입니다.

## 구조 (현재 최소 슬라이스)

- `app/page.tsx` — 랜딩
- `app/problems/page.tsx` — 문제 목록 (Server Component, 백엔드 호출)
- `app/problems/[id]/page.tsx` — 문제 상세 (Server Component)
- `lib/api.ts` — fetch wrapper + 타입

## OpenAPI 타입 자동 동기화

백엔드 변경 시:
```bash
# 1. 루트에서 OpenAPI 스냅샷 갱신
make openapi   # → frontend/openapi.json

# 2. 프론트에서 타입 재생성
cd frontend && npm run types:gen   # → lib/api/schema.gen.ts
```

`npm run dev` / `npm run build` 시 `predev`/`prebuild` 훅으로 자동 실행됨.

> **Windows-side Node + WSL 한계:** WSL에서 Windows 설치 Node(`node.exe`)를 호출하면 한글 경로 + UNC 경로 조합으로 인해 openapi-typescript 내부 redoc의 `fileURLToPath` 가 실패한다. **WSL native Node 설치 권장**: `sudo apt install nodejs npm` 또는 nvm.

## Tailwind v4

설치 완료. `app/globals.css` 상단에 `@import "tailwindcss"` + `@theme` 토큰. 기존 plain CSS 클래스(`card`, `error` 등)는 그대로 유지하면서 신규 컴포넌트는 Tailwind utility 로 작성 가능.

## shadcn/ui (foundation only)

`components.json`, `lib/utils.ts` (cn helper) 만 셋업. 실제 컴포넌트는 다음 슬라이스에서 `npx shadcn add button input ...` 으로 추가.
