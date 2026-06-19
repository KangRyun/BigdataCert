import type { Metadata } from "next";

import Header from "@/components/header";
import { AppProviders } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "빅분기 실기 연습",
  description: "빅데이터분석기사 실기·필기 학습 사이트",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <AppProviders>
          <Header />
          <main>{children}</main>
        </AppProviders>
      </body>
    </html>
  );
}
