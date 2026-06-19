"use client";

import { useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";

interface Props {
  problemId: string;
}

type Status = "idle" | "loading" | "saving" | "saved" | "dirty" | "error";

export default function MyNote({ problemId }: Props) {
  const [content, setContent] = useState("");
  const [status, setStatus] = useState<Status>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setStatus("loading");
    setErrorMessage(null);
    api
      .getMyNote(problemId)
      .then((note) => {
        setContent(note.content);
        setStatus("idle");
      })
      .catch((e) => {
        // 404 = 아직 노트 없음. 빈 상태로 시작
        if (e instanceof ApiError && e.status === 404) {
          setContent("");
          setStatus("idle");
          return;
        }
        setErrorMessage("노트를 불러오지 못했습니다.");
        setStatus("error");
      });
  }, [problemId]);

  async function handleSave() {
    setStatus("saving");
    setErrorMessage(null);
    try {
      await api.upsertMyNote(problemId, content);
      setStatus("saved");
    } catch {
      setErrorMessage("저장에 실패했습니다. 백엔드 상태를 확인하세요.");
      setStatus("error");
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setContent(e.target.value);
    setStatus("dirty");
  }

  return (
    <section className="my-note">
      <div className="my-note-header">
        <h3>내 오답노트</h3>
        <span className="my-note-status">
          {status === "loading" && "불러오는 중…"}
          {status === "saving" && "저장 중…"}
          {status === "saved" && "저장됨"}
          {status === "dirty" && "저장되지 않은 변경 있음"}
          {status === "error" && "오류"}
        </span>
      </div>
      <textarea
        className="my-note-textarea"
        value={content}
        onChange={handleChange}
        placeholder="이 문제에서 막혔던 부분, 핵심 개념, 다음에 시도할 접근을 메모해두세요."
        rows={6}
        maxLength={20000}
        disabled={status === "loading"}
      />
      {errorMessage && <div className="error">{errorMessage}</div>}
      <div className="my-note-actions">
        <button
          type="button"
          className="primary-btn"
          onClick={handleSave}
          disabled={status === "loading" || status === "saving"}
        >
          {status === "saving" ? "저장 중…" : "저장"}
        </button>
        <span className="hint-text">최대 20,000자</span>
      </div>
    </section>
  );
}
