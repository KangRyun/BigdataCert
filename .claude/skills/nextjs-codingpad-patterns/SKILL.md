---
name: nextjs-codingpad-patterns
description: "Next.js 15 App Router 기반 빅분기 학습 UI 구현 패턴. Monaco/CodeMirror 코드 에디터, 문제 마크다운 렌더링, 채점 결과 UI, TanStack Query 훅, OpenAPI 타입 동기화 일체. frontend-engineer가 화면을 구현할 때 반드시 이 스킬을 사용. '문제 페이지', '코드 에디터', '채점 UI', '대시보드', '오답노트 화면', 'Next.js 라우팅', 'API 훅' 같은 요청에도 트리거."
---

# Next.js + Monaco 코딩 UI 구현 패턴

빅분기 실기 연습 사이트의 사용자 인터페이스 구성 표준. App Router·코드 에디터·API 통신·타입 안전성을 일관된 컨벤션으로 묶는다.

## 화면 ↔ 라우트 ↔ API 매핑 (SSOT)

| 화면 | 라우트 | 주요 API | 비고 |
|------|--------|---------|------|
| 랜딩 | `/` | (정적) | RSC |
| 회원가입/로그인 | `/auth/sign-in`, `/auth/sign-up` | `POST /auth/...` | Client |
| 문제 목록 | `/problems` | `GET /problems?type=&difficulty=` | RSC + 클라이언트 필터 |
| 문제 풀이 | `/problems/[id]` | `GET /problems/{id}`, `POST /submissions` | Client (에디터) |
| 진도 대시보드 | `/dashboard` | `GET /me/progress` | Client (차트) |
| 오답노트 | `/notes` | `GET/POST/PATCH/DELETE /me/notes` | Client |

신규 화면 추가 시 이 표를 우선 갱신한다. 표는 frontend ↔ backend 계약의 시각화.

## 디렉토리 구조

```
frontend/
├── app/
│   ├── (marketing)/
│   │   └── page.tsx
│   ├── (auth)/
│   │   ├── sign-in/page.tsx
│   │   └── sign-up/page.tsx
│   ├── (app)/
│   │   ├── layout.tsx           # 사이드바, 인증 가드
│   │   ├── problems/
│   │   │   ├── page.tsx         # 목록 (RSC)
│   │   │   └── [id]/
│   │   │       ├── page.tsx     # 클라이언트 풀이 화면
│   │   │       └── _components/
│   │   │           ├── editor.tsx
│   │   │           ├── problem-pane.tsx
│   │   │           └── grading-result.tsx
│   │   ├── dashboard/page.tsx
│   │   └── notes/page.tsx
│   ├── api/                     # Route Handlers (인증 콜백 등 최소한만)
│   └── layout.tsx
├── components/
│   ├── ui/                      # shadcn/ui
│   ├── markdown/                # ReactMarkdown wrapper
│   └── editor/                  # Monaco wrapper
├── lib/
│   ├── api/
│   │   ├── client.ts            # openapi-fetch
│   │   └── schema.d.ts          # 생성됨 (수동 수정 금지)
│   ├── hooks/                   # TanStack Query
│   ├── stores/                  # zustand
│   └── utils/
└── package.json
```

## 코드 에디터 통합 (Monaco)

```tsx
// components/editor/editor.tsx
"use client";
import dynamic from "next/dynamic";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => <EditorFallback />,
});

export function CodeEditor({
  value,
  onChange,
  onSubmit,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
}) {
  return (
    <MonacoEditor
      height="100%"
      language="python"
      theme="vs-dark"
      value={value}
      onChange={(v) => onChange(v ?? "")}
      options={{
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        tabSize: 4,
        insertSpaces: true,
      }}
      onMount={(editor, monaco) => {
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, onSubmit);
      }}
    />
  );
}
```

> SSR 비활성화 필수 — Monaco는 브라우저 전용. 로딩 중에는 `<textarea>` fallback으로 입력 끊김 방지.

## API 클라이언트 + 훅

```ts
// lib/api/client.ts
import createClient from "openapi-fetch";
import type { paths } from "./schema";   // 생성됨

export const api = createClient<paths>({ baseUrl: process.env.NEXT_PUBLIC_API_BASE });
```

```ts
// lib/hooks/use-problem.ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";

export function useProblem(id: string) {
  return useQuery({
    queryKey: ["problem", id],
    queryFn: async () => {
      const { data, error } = await api.GET("/problems/{id}", {
        params: { path: { id } },
      });
      if (error) throw new ApiError(error);
      return data;
    },
  });
}
```

```ts
// lib/hooks/use-submit.ts
export function useSubmitCode(problemId: string) {
  return useMutation({
    mutationFn: async (code: string) => {
      const { data, error } = await api.POST("/submissions", {
        body: { problem_id: problemId, code },
      });
      if (error) throw new ApiError(error);
      return data;   // { passed, score, metric_name, feedback, error_code? }
    },
  });
}
```

## OpenAPI 타입 동기화

```jsonc
// package.json
{
  "scripts": {
    "types:gen": "openapi-typescript ../backend/_workspace/openapi.json -o lib/api/schema.d.ts",
    "prebuild": "pnpm types:gen",
    "dev": "pnpm types:gen && next dev"
  }
}
```

> 백엔드의 OpenAPI 스냅샷을 매 빌드/dev 시작 시 가져와 타입 생성. 수동 수정한 schema.d.ts는 즉시 덮어쓰여야 함.

## 에러 처리 매핑

```ts
// lib/api/error-map.ts
export const ERROR_MESSAGES: Record<string, string> = {
  TIMEOUT: "실행 시간이 초과되었습니다. (30초 제한)",
  MEMORY: "메모리 한도를 초과했습니다. (512MB 제한)",
  FORBIDDEN_PATTERN: "허용되지 않은 import 또는 함수가 사용되었습니다.",
  RUNTIME_ERROR: "실행 중 에러가 발생했습니다. stderr를 확인하세요.",
  OUTPUT_PARSE: "출력 형식이 기대와 다릅니다.",
  SHAPE_MISMATCH: "제출 파일의 형식(컬럼 등)이 기대와 다릅니다.",
  MISSING_ARTIFACT: "제출 파일(pred.csv 등)을 찾을 수 없습니다.",
  TOLERANCE_FAIL: "결과가 허용 오차를 벗어났습니다.",
};

export function getErrorMessage(code?: string, fallback = "알 수 없는 오류가 발생했습니다."): string {
  return (code && ERROR_MESSAGES[code]) ?? fallback;
}
```

> 이 매핑 테이블은 backend의 error_code 목록과 동기화 필수. qa-integration이 둘을 비교 검증.

## 문제 마크다운 렌더링

```tsx
// components/markdown/renderer.tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import "katex/dist/katex.min.css";

export function ProblemMarkdown({ source }: { source: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        code({ inline, className, children, ...rest }) {
          const match = /language-(\w+)/.exec(className ?? "");
          if (!inline && match) {
            return <SyntaxHighlighter language={match[1]}>{String(children)}</SyntaxHighlighter>;
          }
          return <code {...rest}>{children}</code>;
        },
      }}
    >
      {source}
    </ReactMarkdown>
  );
}
```

## 풀이 화면 레이아웃

데스크탑 기준 좌(문제) / 우(에디터+결과) 2분할.

```
┌───────────────────────────────────────┐
│  헤더 (문제 제목, 난이도, 타이머)        │
├──────────────────┬────────────────────┤
│  문제 본문       │  코드 에디터        │
│  (마크다운)      │  ┌──────────────┐  │
│                  │  │ Monaco       │  │
│  힌트 토글       │  └──────────────┘  │
│                  │  [제출] [힌트]      │
│                  │  ─────────────────  │
│                  │  채점 결과 패널     │
└──────────────────┴────────────────────┘
```

모바일에서는 탭으로 전환 (문제/에디터/결과).

## 상태 관리 규칙

- **서버 상태**: TanStack Query만 사용. SWR·zustand로 중복 보관 금지
- **클라이언트 상태**: zustand 또는 useState로 충분. Context API는 인증·테마 같은 글로벌 한정
- **에디터 코드 임시 저장**: localStorage에 problem_id 별로 저장 (`code:${problem_id}`)

## 접근성 + 한국어

- 모든 인터랙티브 요소에 `aria-label` 한국어로
- 코드 에디터의 lang 속성은 `ko-KR`
- 키보드 단축키 안내는 우상단 헬프 아이콘에서 토글

## QA 회귀 (frontend 측)

- 모든 훅의 응답 타입이 OpenAPI 생성 타입과 일치하는지 빌드 시 검증 (tsc strict)
- 에러 코드 매핑 테이블에 backend의 모든 error_code가 포함됐는지 qa-integration이 회귀 테스트
