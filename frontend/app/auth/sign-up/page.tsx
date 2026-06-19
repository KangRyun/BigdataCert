"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, ERROR_MESSAGES, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function SignUpPage() {
  const router = useRouter();
  const { setAuth } = useAuth();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.register(email, password, displayName);
      setAuth(res.access_token, res.user);
      router.push("/me");
    } catch (e) {
      const code = e instanceof ApiError ? e.errorCode : null;
      if (e instanceof ApiError && e.status === 422) {
        setError("비밀번호는 8~72자, 이메일은 유효한 형식이어야 합니다.");
      } else {
        setError(code ? ERROR_MESSAGES[code] ?? "가입에 실패했습니다." : "가입에 실패했습니다.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <h1>가입</h1>
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
          닉네임
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            maxLength={50}
          />
        </label>
        <label>
          비밀번호 (8~72자)
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            maxLength={72}
            autoComplete="new-password"
          />
        </label>
        {error && <div className="error">{error}</div>}
        <button type="submit" className="primary-btn" disabled={submitting}>
          {submitting ? "가입 중…" : "가입하기"}
        </button>
      </form>
      <p className="auth-aside">
        이미 계정이 있나요? <Link href="/auth/sign-in">로그인 →</Link>
      </p>
    </div>
  );
}
