"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

export default function Header() {
  const { user, loading, clearAuth } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    clearAuth();
    router.push("/");
  }

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link href="/" className="brand">
          빅분기 실기 연습
        </Link>
        <nav className="site-nav">
          <Link href="/problems" className={pathname?.startsWith("/problems") ? "active" : ""}>
            문제
          </Link>
          {user && (
            <>
              <Link
                href="/me"
                className={pathname === "/me" ? "active" : ""}
              >
                내 학습
              </Link>
              <Link
                href="/me/notes"
                className={pathname?.startsWith("/me/notes") ? "active" : ""}
              >
                오답노트
              </Link>
            </>
          )}
          {loading ? null : user ? (
            <>
              <span className="user-chip">{user.display_name}</span>
              <button type="button" className="link-btn" onClick={handleLogout}>
                로그아웃
              </button>
            </>
          ) : (
            <>
              <Link href="/auth/sign-in" className={pathname === "/auth/sign-in" ? "active" : ""}>
                로그인
              </Link>
              <Link href="/auth/sign-up" className={pathname === "/auth/sign-up" ? "active" : ""}>
                가입
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
