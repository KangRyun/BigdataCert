"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

import {
  ApiError,
  ERROR_MESSAGES,
  type GradingResult,
  type ProblemDetail,
  api,
} from "@/lib/api";

import MyHistory from "./my-history";
import MyNote from "./my-note";

const DRAFT_KEY_PREFIX = "bigdata.draft.";
const DRAFT_DEBOUNCE_MS = 600;

function draftKey(pid: string): string {
  return DRAFT_KEY_PREFIX + pid;
}

function formatDraftAge(savedAt: number): string {
  const diff = Date.now() - savedAt;
  if (diff < 5_000) return "방금 임시저장";
  if (diff < 60_000) return `${Math.floor(diff / 1000)}초 전 임시저장`;
  return `${Math.floor(diff / 60_000)}분 전 임시저장`;
}

const CodeEditor = dynamic(() => import("./code-editor"), {
  ssr: false,
  loading: () => <div className="editor-loading">에디터를 불러오는 중…</div>,
});

const EXAM_LABEL: Record<string, string> = {
  practical_1: "작업형 1",
  practical_2: "작업형 2",
  practical_3: "작업형 3",
  written: "필기",
};

const STARTER_CODE_BY_TYPE: Record<string, string> = {
  practical_1: `import pandas as pd

df = pd.read_csv("data.csv")

# TODO: 답을 계산해 마지막 줄에 print 하세요.
`,
  practical_2: `import pandas as pd
from sklearn.ensemble import RandomForestClassifier

train = pd.read_csv("train.csv")
test = pd.read_csv("test.csv")

# TODO: 전처리 → 학습 → 예측 → pred.csv 저장
`,
  practical_3: `import pandas as pd
import scipy.stats as stats

df = pd.read_csv("data.csv")

# TODO: 검정 통계량과 p-value 를 계산해 dict로 print 하세요.
`,
  written: `# 정답 번호(1-4)를 print 하세요.
`,
};

function getStarter(p: ProblemDetail): string {
  return STARTER_CODE_BY_TYPE[p.exam_type] ?? "# 코드를 작성하세요.\n";
}

export default function ProblemSolver({ problem }: { problem: ProblemDetail }) {
  const { data: session } = useSession();
  const user = session?.user;
  // SSR 초기값은 starter 로 통일해 hydration mismatch 회피. 마운트 후 localStorage 에서 복구.
  const [code, setCode] = useState<string>(() => getStarter(problem));
  const [draftRestored, setDraftRestored] = useState(false);
  const [draftSavedAt, setDraftSavedAt] = useState<number | null>(null);
  const [result, setResult] = useState<GradingResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hintsRevealed, setHintsRevealed] = useState(0);
  const [submitCount, setSubmitCount] = useState(0);

  // 마운트 시 임시저장 복구
  useEffect(() => {
    try {
      const saved = localStorage.getItem(draftKey(problem.problem_id));
      if (saved && saved.length > 0) {
        setCode(saved);
        setDraftSavedAt(Date.now());
      }
    } catch {
      /* storage 비활성 환경은 무시 */
    }
    setDraftRestored(true);
    // problem.problem_id 가 바뀔 가능성은 라우팅상 거의 없지만 안전 차원에서 dep.
  }, [problem.problem_id]);

  // 코드 변경 시 debounced 저장
  useEffect(() => {
    if (!draftRestored) return;
    const t = setTimeout(() => {
      try {
        localStorage.setItem(draftKey(problem.problem_id), code);
        setDraftSavedAt(Date.now());
      } catch {
        /* ignore */
      }
    }, DRAFT_DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [code, draftRestored, problem.problem_id]);

  function resetDraft() {
    const ok =
      typeof window === "undefined" ||
      window.confirm("작성 중인 코드를 모두 지우고 시작 템플릿으로 되돌릴까요?");
    if (!ok) return;
    setCode(getStarter(problem));
    try {
      localStorage.removeItem(draftKey(problem.problem_id));
    } catch {
      /* ignore */
    }
    setDraftSavedAt(null);
  }

  async function handleSubmit() {
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const r = await api.submit(problem.problem_id, code);
      setResult(r);
      setSubmitCount((c) => c + 1);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? `백엔드 호출 실패 (status ${e.status})`
          : "백엔드에 연결할 수 없습니다.";
      setError(msg);
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  }

  function revealNextHint() {
    setHintsRevealed((n) => Math.min(n + 1, problem.hints.length));
  }

  return (
    <>
      <p>
        <Link href="/problems">← 목록</Link>
      </p>
      <h1>{problem.title}</h1>
      <div className="card-meta" style={{ marginBottom: "1.5rem" }}>
        <span>{EXAM_LABEL[problem.exam_type] ?? problem.exam_type}</span>
        <span>·</span>
        <span className={`badge badge-${problem.difficulty}`}>{problem.difficulty}</span>
        <span>·</span>
        <span>{problem.topic_tags.join(", ")}</span>
      </div>

      <h2>문제</h2>
      <div className="problem-body">{problem.description}</div>

      {problem.hints.length > 0 && (
        <>
          <h2>힌트</h2>
          {hintsRevealed === 0 ? (
            <p style={{ color: "var(--muted)" }}>
              막혔을 때만 단계적으로 열어보세요.{" "}
              <button className="link-btn" onClick={revealNextHint}>
                힌트 1단계 보기
              </button>
            </p>
          ) : (
            <>
              <ol className="hint-list">
                {problem.hints.slice(0, hintsRevealed).map((hint, i) => (
                  <li key={i}>{hint}</li>
                ))}
              </ol>
              {hintsRevealed < problem.hints.length && (
                <button className="link-btn" onClick={revealNextHint}>
                  다음 힌트 보기 ({hintsRevealed}/{problem.hints.length})
                </button>
              )}
            </>
          )}
        </>
      )}

      <h2>풀이 코드</h2>
      <div className="editor-shell">
        <CodeEditor value={code} onChange={setCode} onSubmit={handleSubmit} />
      </div>
      <div className="submit-row">
        <button
          type="button"
          className="primary-btn"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? "채점 중…" : "제출 (Ctrl+Enter)"}
        </button>
        <button type="button" className="link-btn" onClick={resetDraft}>
          초기화
        </button>
        <span className="hint-text">
          format: <code>{problem.expected_output.format}</code>
          {problem.expected_output.metric && (
            <>
              {" "}· metric: <code>{problem.expected_output.metric}</code>
            </>
          )}
        </span>
        {draftSavedAt !== null && (
          <span className="draft-indicator" title="브라우저 localStorage 에 저장됨">
            {formatDraftAge(draftSavedAt)}
          </span>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className={result.passed ? "result-pass" : "result-fail"}>
          <div className="result-headline">
            <span className="result-badge">{result.passed ? "PASS" : "FAIL"}</span>
            <span>
              {result.metric_name} · score {result.score.toFixed(2)}
            </span>
          </div>
          <div className="result-feedback">{result.feedback}</div>
          {result.error_code && (
            <div className="result-error-code">
              error_code: <code>{result.error_code}</code> —{" "}
              {ERROR_MESSAGES[result.error_code] ?? "추가 정보 없음"}
            </div>
          )}
        </div>
      )}

      {user && (
        <>
          <MyHistory problemId={problem.problem_id} refreshKey={submitCount} />
          <MyNote problemId={problem.problem_id} />
        </>
      )}
    </>
  );
}
