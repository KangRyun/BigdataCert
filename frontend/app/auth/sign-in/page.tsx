"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";
import { Suspense, useState } from "react";

const GOOGLE_ENABLED = process.env.NEXT_PUBLIC_GOOGLE_ENABLED === "1";

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/me";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });
    setSubmitting(false);
    if (res?.error || !res?.ok) {
      setError("이메일 또는 비밀번호가 올바르지 않습니다.");
      return;
    }
    router.push(callbackUrl);
  }

  function handleGoogle() {
    signIn("google", { callbackUrl });
  }

  return (
    <>
      {GOOGLE_ENABLED && (
        <>
          <button
            type="button"
            className="google-btn"
            onClick={handleGoogle}
            disabled={submitting}
          >
            <span aria-hidden>🅖</span> Google 계정으로 계속하기
          </button>
          <div className="auth-divider"><span>또는</span></div>
        </>
      )}

      <form onSubmit={handleEmail} className="auth-form">
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
    </>
  );
}

export default function SignInPage() {
  return (
    <div className="auth-shell">
      <h1>로그인</h1>
      <Suspense fallback={<p className="hint-text">불러오는 중…</p>}>
        <SignInForm />
      </Suspense>
    </div>
  );
}
