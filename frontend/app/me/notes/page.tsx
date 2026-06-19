"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, type MyNote, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

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

function snippet(content: string, max = 140): string {
  const compact = content.replace(/\s+/g, " ").trim();
  return compact.length > max ? compact.slice(0, max) + "…" : compact;
}

export default function NotesIndexPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [notes, setNotes] = useState<MyNote[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/auth/sign-in");
      return;
    }
    api
      .listMyNotes()
      .then(setNotes)
      .catch((e) =>
        setError(
          e instanceof ApiError
            ? `노트를 불러오지 못했습니다. (status ${e.status})`
            : "백엔드 연결 실패",
        ),
      );
  }, [authLoading, user, router]);

  if (authLoading || !user) return null;

  return (
    <>
      <h1>오답노트</h1>
      <p className="subtitle">{user.display_name} 님의 학습 메모.</p>

      {error && <div className="error">{error}</div>}

      {notes === null ? (
        <p className="hint-text">불러오는 중…</p>
      ) : notes.length === 0 ? (
        <p className="hint-text">
          아직 작성한 노트가 없습니다. <Link href="/problems">문제를 풀러 가세요 →</Link>
        </p>
      ) : (
        <ul className="note-list">
          {notes.map((n) => (
            <li key={n.id} className="note-card">
              <Link href={`/problems/${n.problem_id}`} className="note-problem">
                {n.problem_id}
              </Link>
              <div className="note-snippet">
                {n.content.trim() ? snippet(n.content) : <em>(빈 메모)</em>}
              </div>
              <time className="note-time">최근 수정: {formatDate(n.updated_at)}</time>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
