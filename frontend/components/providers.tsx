"use client";

import { SessionProvider } from "next-auth/react";
import { useEffect } from "react";
import { useSession } from "next-auth/react";

import { setAuthToken } from "@/lib/api";

/**
 * useSession 의 accessToken 을 lib/api 의 모듈 전역 변수와 동기화.
 * 모든 fetch 가 Bearer 토큰을 자동으로 첨부하게 됨.
 */
function SessionTokenSync({ children }: { children: React.ReactNode }) {
  const { data, status } = useSession();
  useEffect(() => {
    if (status === "loading") return;
    setAuthToken(data?.accessToken ?? null);
  }, [data?.accessToken, status]);
  return <>{children}</>;
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <SessionTokenSync>{children}</SessionTokenSync>
    </SessionProvider>
  );
}
