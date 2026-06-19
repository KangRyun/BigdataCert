"use client";

import { useEffect, useState } from "react";

import { ApiError, type MeSubmission, api } from "@/lib/api";

interface Props {
  problemId: string;
  /** 부모가 제출 후 증가시키면 자동 재조회 */
  refreshKey: number;
}

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diffMs / 60_000);
  if (min < 1) return "방금 전";
  if (min < 60) return `${min}분 전`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}시간 전`;
  const days = Math.floor(hr / 24);
  return `${days}일 전`;
}

export default function MyHistory({ problemId, refreshKey }: Props) {
  const [items, setItems] = useState<MeSubmission[] | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api
      .mySubmissions({ problem_id: problemId, limit: 20 })
      .then(setItems)
      .catch((e) => {
        // 비로그인 / 401 은 상위 가드에서 처리 — 여기서는 조용히 패스
        if (!(e instanceof ApiError) || e.status !== 401) {
          console.warn("history fetch failed", e);
        }
        setItems([]);
      });
  }, [problemId, refreshKey]);

  if (!items) return null;

  const total = items.length;
  const passed = items.filter((s) => s.passed).length;

  return (
    <section className="my-history">
      <button
        type="button"
        className="my-history-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        내 이력 {total}건{total > 0 && <> · PASS {passed}</>} {open ? "▾" : "▸"}
      </button>
      {open && items.length > 0 && (
        <ul className="my-history-list">
          {items.map((s) => (
            <li key={s.id} className="my-history-row">
              <span className={s.passed ? "submission-pass" : "submission-fail"}>
                {s.passed ? "PASS" : "FAIL"}
              </span>
              <span className="my-history-meta">
                {s.metric_name} · {s.score.toFixed(2)}
              </span>
              <time className="my-history-time">{timeAgo(s.created_at)}</time>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
