import Link from "next/link";

import { ApiError, api, type Difficulty } from "@/lib/api";

const EXAM_LABEL: Record<string, string> = {
  practical_1: "작업형 1",
  practical_2: "작업형 2",
  practical_3: "작업형 3",
  written: "필기",
};

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

export default async function ProblemsPage() {
  try {
    const problems = await api.listProblems();
    if (problems.length === 0) {
      return (
        <>
          <h1>문제 목록</h1>
          <p className="subtitle">아직 등록된 문제가 없습니다.</p>
        </>
      );
    }
    return (
      <>
        <h1>문제 목록</h1>
        <p className="subtitle">전체 {problems.length}문항</p>
        {problems.map((p) => (
          <Link key={p.problem_id} href={`/problems/${p.problem_id}`} className="card">
            <div className="card-title">{p.title}</div>
            <div className="card-meta">
              <span>{EXAM_LABEL[p.exam_type] ?? p.exam_type}</span>
              <span>·</span>
              <span className={`badge badge-${p.difficulty}`}>
                {DIFFICULTY_LABEL[p.difficulty]}
              </span>
              <span>·</span>
              <span>{p.topic_tags.join(", ")}</span>
            </div>
          </Link>
        ))}
      </>
    );
  } catch (err) {
    const message =
      err instanceof ApiError
        ? `백엔드 호출 실패 (status ${err.status})`
        : "백엔드에 연결할 수 없습니다.";
    return (
      <>
        <h1>문제 목록</h1>
        <div className="error">
          <strong>{message}</strong>
          <p>
            백엔드 서버가 <code>http://localhost:8000</code>에서 실행 중인지 확인하세요. <br />
            <code>cd backend && uvicorn app.main:app --reload</code>
          </p>
        </div>
      </>
    );
  }
}
