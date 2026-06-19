import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  // typedRoutes 는 NextAuth callbackUrl 등 외부 입력 URL 과 충돌이 많아 보류.
  // 필요해지면 향후 string-as-Route cast 헬퍼와 함께 재도입.
};

export default config;
