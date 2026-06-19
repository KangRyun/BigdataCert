import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <h1>빅분기 실기 연습</h1>
      <p className="subtitle">
        빅데이터분석기사 실기·필기 시험을 위한 학습 플랫폼. 작업형 1·2·3과 필기 이론을 한 곳에서.
      </p>
      <p>
        <Link href="/problems">문제 풀어보기 →</Link>
      </p>
    </>
  );
}
