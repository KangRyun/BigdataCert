"""스칼라 채점기.

사용자 코드의 stdout 마지막 줄을 float로 파싱해 expected.answer 와 비교.
tolerance 는 절대/상대 모두에 사용 (rel_tol=tolerance, abs_tol=max(tolerance, 1e-9)).
"""

import math

from app.grading.base import GradingResult
from app.sandbox import SandboxResult
from app.schemas.problem import ExpectedOutput


def grade_scalar(spec: ExpectedOutput, result: SandboxResult) -> GradingResult:
    if spec.answer is None:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="scalar",
            error_code="SPEC_MISSING_ANSWER",
            feedback="문제 정의에 정답 값이 없습니다. 관리자에게 문의하세요.",
        )

    text = result.stdout.strip()
    if not text:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="scalar",
            error_code="OUTPUT_PARSE",
            feedback="출력이 비어 있습니다. 답을 print 하세요.",
        )

    last_line = text.splitlines()[-1].strip()
    try:
        submitted = float(last_line)
    except ValueError:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="scalar",
            error_code="OUTPUT_PARSE",
            feedback=f"출력의 마지막 줄을 숫자로 해석할 수 없습니다: {last_line[:80]!r}",
        )

    expected = float(spec.answer)  # type: ignore[arg-type]
    tol = spec.tolerance or 0.0

    if math.isclose(submitted, expected, rel_tol=tol, abs_tol=max(tol, 1e-9)):
        return GradingResult(
            passed=True,
            score=1.0,
            metric_name="scalar",
            feedback=f"정답입니다. (제출: {submitted:g})",
        )

    return GradingResult(
        passed=False,
        score=0.0,
        metric_name="scalar",
        feedback=f"기대값과 다릅니다. (제출: {submitted:g}, 기댓값: {expected:g} ± {tol:g})",
    )
