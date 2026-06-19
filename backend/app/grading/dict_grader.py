"""딕셔너리 산출물 채점 — 작업형 3.

학습자가 stdout 마지막 줄에 dict 를 print 하면, ast.literal_eval 로 파싱해
spec.answer 와 키별로 isclose 비교.
"""

import ast
import math

from app.grading.base import GradingResult
from app.sandbox import SandboxResult
from app.schemas.problem import ExpectedOutput


def grade_dict(spec: ExpectedOutput, result: SandboxResult) -> GradingResult:
    if not isinstance(spec.answer, dict):
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="dict",
            error_code="SPEC_MISSING_ANSWER",
            feedback="문제 정의에 정답 딕셔너리가 없습니다.",
        )

    text = result.stdout.strip()
    if not text:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="dict",
            error_code="OUTPUT_PARSE",
            feedback="출력이 비어 있습니다. 정답을 dict 로 print 하세요.",
        )

    last_line = text.splitlines()[-1].strip()
    try:
        parsed = ast.literal_eval(last_line)
    except (ValueError, SyntaxError) as exc:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="dict",
            error_code="OUTPUT_PARSE",
            feedback=f"출력 마지막 줄을 dict 로 해석할 수 없습니다: {exc}",
        )

    if not isinstance(parsed, dict):
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="dict",
            error_code="OUTPUT_PARSE",
            feedback=f"마지막 줄이 dict 가 아닙니다 ({type(parsed).__name__}).",
        )

    tol = spec.tolerance or 0.0
    abs_tol = max(tol, 1e-9)
    misses: list[str] = []

    for key, expected_value in spec.answer.items():
        if key not in parsed:
            misses.append(f"키 누락: {key}")
            continue
        try:
            submitted = float(parsed[key])
            expected = float(expected_value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            misses.append(f"{key}: 비교할 수 없는 값 ({parsed[key]} vs {expected_value})")
            continue
        if not math.isclose(submitted, expected, rel_tol=tol, abs_tol=abs_tol):
            misses.append(
                f"{key}: 제출 {submitted:g} vs 기대 {expected:g} (허용 ±{tol:g})"
            )

    if misses:
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name="dict",
            feedback="다음 항목이 불일치합니다:\n- " + "\n- ".join(misses),
        )

    return GradingResult(
        passed=True,
        score=1.0,
        metric_name="dict",
        feedback="정답입니다. 모든 키 일치.",
    )
