"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, ERROR_MESSAGES, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function SignInPage() {
  const router = useRouter();
  const { setAuth } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.login(email, password);
      setAuth(res.access_token, res.user);
      router.push("/me");
    } catch (e) {
      const code = e instanceof ApiError ? e.errorCode : null;
      setError(code ? ERROR_MESSAGES[code] ?? "로그인에 실패했습니다." : "로그인에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <h1>로그인</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <label>
          이메일
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </label>
        <label>
          비밀번호
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        {error && <div className="error">{error}</div>}
        <button type="submit" className="primary-btn" disabled={submitting}>
          {submitting ? "로그인 중…" : "로그인"}
        </button>
      </form>
      <p className="auth-aside">
        아직 가입하지 않았나요? <Link href="/auth/sign-up">가입하기 →</Link>
      </p>
    </div>
  );
}
