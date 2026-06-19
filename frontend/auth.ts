/**
 * NextAuth v5 (= Auth.js v5) 설정.
 *
 * 전략: JWT 세션. 백엔드(FastAPI)가 발급한 JWT 를 NextAuth 세션의 accessToken
 * 으로 보관한다. 두 provider:
 *  - Credentials: 이메일/비번 → 백엔드 /auth/login 호출
 *  - Google: Google OAuth → ID token → 백엔드 /auth/google 호출 (검증 + JWT 발급)
 *
 * AUTH_SECRET 은 백엔드 JWT_SECRET 과 동일해야 (이후 7b 슬라이스에서)
 * 백엔드 보호 엔드포인트가 NextAuth 세션 토큰을 검증 가능.
 */

import NextAuth, { type DefaultSession } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";

interface BackendUserPayload {
  id: number;
  email: string;
  display_name: string;
}

interface BackendTokenResponse {
  access_token: string;
  token_type: string;
  user: BackendUserPayload;
}

async function callBackend(path: string, body: unknown): Promise<BackendTokenResponse | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) return null;
    return (await res.json()) as BackendTokenResponse;
  } catch {
    return null;
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  trustHost: true,
  providers: [
    Google,
    Credentials({
      name: "이메일/비번",
      credentials: {
        email: { label: "이메일", type: "email" },
        password: { label: "비밀번호", type: "password" },
      },
      async authorize(credentials) {
        const email = credentials?.email as string | undefined;
        const password = credentials?.password as string | undefined;
        if (!email || !password) return null;

        const data = await callBackend("/auth/login", { email, password });
        if (!data) return null;

        return {
          id: String(data.user.id),
          email: data.user.email,
          name: data.user.display_name,
          accessToken: data.access_token,
        };
      },
    }),
  ],
  callbacks: {
    /**
     * Google sign-in 직후 백엔드 /auth/google 을 호출해 우리 JWT 를 받아온다.
     * 받은 토큰은 user 객체에 첨부되어 다음 jwt callback 에서 token 으로 옮겨진다.
     */
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        const idToken = (account as { id_token?: string }).id_token;
        if (!idToken) return false;
        const data = await callBackend("/auth/google", { id_token: idToken });
        if (!data) return false;
        user.id = String(data.user.id);
        user.name = data.user.display_name;
        user.email = data.user.email;
        (user as { accessToken?: string }).accessToken = data.access_token;
      }
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        const u = user as { accessToken?: string };
        if (u.accessToken) token.accessToken = u.accessToken;
        if (user.id) token.userId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (token.accessToken) session.accessToken = token.accessToken as string;
      if (token.userId && session.user) {
        (session.user as { id?: string }).id = token.userId as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/auth/sign-in",
  },
});

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    user?: {
      id?: string;
    } & DefaultSession["user"];
  }
}

declare module "@auth/core/jwt" {
  interface JWT {
    accessToken?: string;
    userId?: string;
  }
}
