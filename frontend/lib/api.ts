/**
 * 백엔드 API 클라이언트 (최소 버전).
 *
 * 다음 단계에서 openapi-typescript 로 타입 자동 생성 + openapi-fetch 도입 예정.
 * 현재는 수동 타입.
 */

const SERVER_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";
const CLIENT_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function baseUrl(): string {
  return typeof window === "undefined" ? SERVER_BASE : CLIENT_BASE;
}

export type ExamType = "practical_1" | "practical_2" | "practical_3" | "written";
export type Difficulty = "easy" | "medium" | "hard";

export interface ProblemSummary {
  problem_id: string;
  exam_type: ExamType;
  title: string;
  difficulty: Difficulty;
  topic_tags: string[];
}

export interface ExpectedOutput {
  format: "scalar" | "csv" | "dict" | "choice";
  schema?: string | Record<string, unknown> | null;
  tolerance: number;
  metric?: string | null;
  baseline?: number | null;
  answer?: number | string | Record<string, unknown> | unknown[] | null;
}

export interface ProblemDetail extends ProblemSummary {
  description: string;
  sample_data: Record<string, string>;
  expected_output: ExpectedOutput;
  hints: string[];
}

export class ApiError extends Error {
  constructor(public status: number, public errorCode: string | null, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    let errorCode: string | null = null;
    try {
      const body = await res.json();
      errorCode = body?.detail?.error_code ?? null;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, errorCode, `GET ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  listProblems: (params?: { exam_type?: ExamType; difficulty?: Difficulty }) => {
    const qs = new URLSearchParams();
    if (params?.exam_type) qs.set("exam_type", params.exam_type);
    if (params?.difficulty) qs.set("difficulty", params.difficulty);
    const suffix = qs.toString() ? `?${qs}` : "";
    return get<ProblemSummary[]>(`/problems${suffix}`);
  },
  getProblem: (id: string) => get<ProblemDetail>(`/problems/${encodeURIComponent(id)}`),
};
