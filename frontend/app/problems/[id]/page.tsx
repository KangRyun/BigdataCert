import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, api } from "@/lib/api";

const EXAM_LABEL: Record<string, string> = {
  practical_1: "작업형 1",
  practical_2: "작업형 2",
  practical_3: "작업형 3",
  written: "필기",
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function ProblemDetailPage({ params }: PageProps) {
  const { id } = await params;

  try {
    const problem = await api.getProblem(id);
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
            <h2>힌트 ({problem.hints.length}단계)</h2>
            <ol className="hint-list">
              {problem.hints.map((hint, i) => (
                <li key={i}>{hint}</li>
              ))}
            </ol>
          </>
        )}

        <h2>제출 형식</h2>
        <p>
          <code>format: {problem.expected_output.format}</code>
          {problem.expected_output.metric && (
            <>
              {" · "}
              <code>metric: {problem.expected_output.metric}</code>
            </>
          )}
        </p>

        <p style={{ color: "var(--muted)", marginTop: "2rem" }}>
          코드 에디터·제출·채점 기능은 다음 단계에서 추가됩니다.
        </p>
      </>
    );
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return (
      <div className="error">
        <strong>문제를 불러오지 못했습니다.</strong>
        <p>백엔드 서버 상태를 확인하세요.</p>
      </div>
    );
  }
}
