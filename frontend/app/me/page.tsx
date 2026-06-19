"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

import {
  ApiError,
  type MeSubmission,
  type ProgressResponse,
  api,
} from "@/lib/api";

const EXAM_LABEL: Record<keyof ProgressResponse, string> = {
  practical_1: "작업형 1",
  practical_2: "작업형 2",
  practical_3: "작업형 3",
  written: "필기",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function MyPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [submissions, setSubmissions] = useState<MeSubmission[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    if (status === "unauthenticated") {
      router.replace("/auth/sign-in?callbackUrl=/me");
      return;
    }
    Promise.all([api.myProgress(), api.mySubmissions({ limit: 20 })])
      .then(([p, s]) => {
        setProgress(p);
        setSubmissions(s);
      })
      .catch((e) =>
        setError(
          e instanceof ApiError
            ? `데이터 불러오기 실패 (status ${e.status})`
            : "백엔드 연결 실패",
        ),
      );
  }, [status, router]);

  if (status !== "authenticated") return null;

  const user = session.user;

  return (
    <>
      <h1>내 학습</h1>
      <p className="subtitle">{user?.name ?? user?.email} 님 환영합니다.</p>

      <h2>유형별 진도</h2>
      {!progress ? (
        <p className="hint-text">불러오는 중…</p>
      ) : (
        <div className="progress-grid">
          {(Object.keys(EXAM_LABEL) as (keyof ProgressResponse)[]).map((et) => {
            const p = progress[et];
            return (
              <div key={et} className="progress-card">
                <div className="progress-label">{EXAM_LABEL[et]}</div>
                <div className="progress-numbers">
                  <span>해결 {p.solved}</span>
                  <span>·</span>
                  <span>통과 {p.passed_attempts}</span>
                  <span>·</span>
                  <span>시도 {p.attempts}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <h2>최근 제출</h2>
      {error && <div className="error">{error}</div>}
      {submissions === null ? (
        <p className="hint-text">불러오는 중…</p>
      ) : submissions.length === 0 ? (
        <p className="hint-text">
          아직 제출한 문제가 없습니다. <Link href="/problems">문제 풀러 가기 →</Link>
        </p>
      ) : (
        <ul className="submission-list">
          {submissions.map((s) => (
            <li key={s.id} className="submission-row">
              <Link href={`/problems/${s.problem_id}`} className="submission-problem">
                {s.problem_id}
              </Link>
              <span className={s.passed ? "submission-pass" : "submission-fail"}>
                {s.passed ? "PASS" : "FAIL"}
              </span>
              <span className="submission-meta">
                {s.metric_name} · {s.score.toFixed(2)}
              </span>
              <time className="submission-time">{formatDate(s.created_at)}</time>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
