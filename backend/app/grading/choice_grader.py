"""객관식 채점 — 필기.

stdout 마지막 줄의 정수와 spec.answer 비교.
"""

from app.grading.base import GradingResult
from app.sandbox import SandboxResult
from app.schemas.problem import ExpectedOutput


def grade_choice(spec: ExpectedOutput, result: SandboxResult) -> GradingResult:
    if spec.answer is None:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="choice",
            error_code="SPEC_MISSING_ANSWER",
            feedback="문제 정의에 정답이 없습니다.",
        )

    text = result.stdout.strip()
    if not text:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="choice",
            error_code="OUTPUT_PARSE",
            feedback="출력이 비어 있습니다. 정답 번호(1~4)를 print 하세요.",
        )

    last_line = text.splitlines()[-1].strip()
    try:
        submitted = int(last_line)
    except ValueError:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="choice",
            error_code="OUTPUT_PARSE",
            feedback=f"출력 마지막 줄이 정수가 아닙니다: {last_line!r}",
        )

    expected = int(spec.answer)  # type: ignore[arg-type]
    if submitted == expected:
        return GradingResult(
            passed=True, score=1.0, metric_name="choice", feedback="정답입니다."
        )
    return GradingResult(
        passed=False,
        score=0.0,
        metric_name="choice",
        feedback=f"오답입니다. (제출: {submitted})",
    )
