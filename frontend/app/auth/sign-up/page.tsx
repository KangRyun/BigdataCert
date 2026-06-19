"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { signIn } from "next-auth/react";
import { useState } from "react";

import { ApiError, ERROR_MESSAGES, api } from "@/lib/api";

const GOOGLE_ENABLED = process.env.NEXT_PUBLIC_GOOGLE_ENABLED === "1";

export default function SignUpPage() {
  const router = useRouter();
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
      // 1) 백엔드에 직접 가입 요청 (NextAuth Credentials provider 가 register 를 안 함)
      await api.register(email, password, displayName);
      // 2) 가입 성공 → 같은 자격으로 Credentials sign-in
      const res = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });
      if (!res?.ok) throw new Error("auto sign-in failed");
      router.push("/me");
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) {
        setError("비밀번호는 8~72자, 이메일은 유효한 형식이어야 합니다.");
      } else if (e instanceof ApiError && e.errorCode === "EMAIL_TAKEN") {
        setError(ERROR_MESSAGES.EMAIL_TAKEN);
      } else {
        setError("가입에 실패했습니다.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleGoogle() {
    signIn("google", { callbackUrl: "/me" });
  }

  return (
    <div className="auth-shell">
      <h1>가입</h1>

      {GOOGLE_ENABLED && (
        <>
          <button
            type="button"
            className="google-btn"
            onClick={handleGoogle}
            disabled={submitting}
          >
            <span aria-hidden>🅖</span> Google 계정으로 시작하기
          </button>
          <div className="auth-divider"><span>또는 이메일로 가입</span></div>
        </>
      )}

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
