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

export interface GradingResult {
  passed: boolean;
  score: number;
  metric_name: string;
  feedback: string;
  error_code: string | null;
}

export interface AuthUser {
  id: number;
  email: string;
  display_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface MeSubmission {
  id: number;
  problem_id: string;
  passed: boolean;
  score: number;
  metric_name: string;
  feedback: string;
  error_code: string | null;
  created_at: string;
}

export interface TypeProgress {
  attempts: number;
  passed_attempts: number;
  solved: number;
}

export interface ProgressResponse {
  practical_1: TypeProgress;
  practical_2: TypeProgress;
  practical_3: TypeProgress;
  written: TypeProgress;
}

export interface MyNote {
  id: number;
  problem_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export class ApiError extends Error {
  constructor(public status: number, public errorCode: string | null, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// 인증 토큰은 모듈 전역에 보관 — AuthProvider 가 동기화한다.
let _authToken: string | null = null;
export function setAuthToken(token: string | null) {
  _authToken = token;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init.headers as Record<string, string> | undefined) ?? {}),
  };
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const res = await fetch(`${baseUrl()}${path}`, {
    cache: "no-store",
    ...init,
    headers,
  });
  if (!res.ok) {
    let errorCode: string | null = null;
    try {
      const body = await res.json();
      errorCode = body?.detail?.error_code ?? null;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, errorCode, `${init.method ?? "GET"} ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  listProblems: (params?: { exam_type?: ExamType; difficulty?: Difficulty }) => {
    const qs = new URLSearchParams();
    if (params?.exam_type) qs.set("exam_type", params.exam_type);
    if (params?.difficulty) qs.set("difficulty", params.difficulty);
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<ProblemSummary[]>(`/problems${suffix}`);
  },
  getProblem: (id: string) =>
    request<ProblemDetail>(`/problems/${encodeURIComponent(id)}`),
  submit: (problem_id: string, code: string) =>
    request<GradingResult>("/submissions", {
      method: "POST",
      body: JSON.stringify({ problem_id, code }),
    }),
  register: (email: string, password: string, display_name: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<AuthUser>("/auth/me"),
  mySubmissions: (params?: { problem_id?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.problem_id) qs.set("problem_id", params.problem_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<MeSubmission[]>(`/me/submissions${suffix}`);
  },
  myProgress: () => request<ProgressResponse>("/me/progress"),
  listMyNotes: () => request<MyNote[]>("/me/notes"),
  getMyNote: (problem_id: string) =>
    request<MyNote>(`/me/notes/${encodeURIComponent(problem_id)}`),
  upsertMyNote: (problem_id: string, content: string) =>
    request<MyNote>(`/me/notes/${encodeURIComponent(problem_id)}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
  deleteMyNote: (problem_id: string) =>
    fetch(`${baseUrl()}/me/notes/${encodeURIComponent(problem_id)}`, {
      method: "DELETE",
      headers: _authToken ? { Authorization: `Bearer ${_authToken}` } : undefined,
    }).then((res) => {
      if (!res.ok) throw new ApiError(res.status, null, "DELETE note failed");
    }),
};

export const ERROR_MESSAGES: Record<string, string> = {
  TIMEOUT: "실행 시간이 초과되었습니다. (30초 제한)",
  FORBIDDEN_PATTERN: "허용되지 않은 import 또는 함수가 사용되었습니다.",
  RUNTIME_ERROR: "실행 중 에러가 발생했습니다. stderr를 확인하세요.",
  OUTPUT_PARSE: "출력 형식이 기대와 다릅니다.",
  PROBLEM_NOT_FOUND: "해당 문제를 찾을 수 없습니다.",
  UNSUPPORTED_FORMAT: "이 문제의 채점기는 아직 구현되지 않았습니다.",
  SPEC_MISSING_ANSWER: "문제 정의에 정답이 없습니다. 관리자에게 문의하세요.",
  EMAIL_TAKEN: "이미 가입된 이메일입니다.",
  INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다.",
  AUTH_REQUIRED: "로그인이 필요합니다.",
  MISSING_ARTIFACT: "제출 파일(pred.csv 등)을 찾을 수 없습니다.",
  SHAPE_MISMATCH: "제출 파일의 형식이 기대와 다릅니다.",
  NOTE_NOT_FOUND: "노트가 아직 없습니다.",
};
