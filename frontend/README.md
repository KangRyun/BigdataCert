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

## 다음 단계

- Monaco 코드 에디터 통합
- TanStack Query 도입 (제출·채점 mutation)
- shadcn/ui + Tailwind 도입
- OpenAPI 타입 자동 생성 (openapi-typescript)
