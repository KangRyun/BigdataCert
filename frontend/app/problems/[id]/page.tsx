import { notFound } from "next/navigation";

import { ApiError, api } from "@/lib/api";

import ProblemSolver from "./_components/problem-solver";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function ProblemDetailPage({ params }: PageProps) {
  const { id } = await params;

  try {
    const problem = await api.getProblem(id);
    return <ProblemSolver problem={problem} />;
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return (
      <div className="error">
        <strong>문제를 불러오지 못했습니다.</strong>
        <p>
          백엔드 서버가 <code>http://localhost:8000</code>에서 실행 중인지 확인하세요.
        </p>
      </div>
    );
  }
}
