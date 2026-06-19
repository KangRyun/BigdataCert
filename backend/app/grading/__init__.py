"""채점 엔진.

샌드박스 결과(SandboxResult)와 문제의 expected_output 스키마를 받아 GradingResult를 반환.
format 별 그레이더를 분배한다 (scalar, csv, dict, choice).
"""

from pathlib import Path

from app.grading.base import GradingResult
from app.grading.choice_grader import grade_choice
from app.grading.csv_grader import grade_csv
from app.grading.dict_grader import grade_dict
from app.grading.scalar import grade_scalar
from app.sandbox import SandboxResult
from app.schemas.problem import ExpectedOutput

_ERROR_FEEDBACK = {
    "FORBIDDEN_PATTERN": "허용되지 않은 import 또는 함수가 사용되었습니다. 허용 라이브러리: pandas, numpy, sklearn, scipy, statsmodels, matplotlib.",
    "TIMEOUT": "실행 시간이 초과되었습니다. (30초 제한)",
}


def grade(
    spec: ExpectedOutput,
    result: SandboxResult,
    truth_paths: dict[str, Path] | None = None,
) -> GradingResult:
    if result.error_code:
        feedback = _ERROR_FEEDBACK.get(result.error_code) or (
            result.stderr[-500:] if result.stderr else "실행 중 에러가 발생했습니다."
        )
        return GradingResult(
            passed=False,
            score=0.0,
            metric_name=spec.format,
            error_code=result.error_code,
            feedback=feedback,
        )

    if spec.format == "scalar":
        return grade_scalar(spec, result)
    if spec.format == "csv":
        return grade_csv(spec, result, truth_paths or {})
    if spec.format == "dict":
        return grade_dict(spec, result)
    if spec.format == "choice":
        return grade_choice(spec, result)

    return GradingResult(
        passed=False,
        score=0.0,
        metric_name=spec.format,
        error_code="UNSUPPORTED_FORMAT",
        feedback=f"이 문제 유형(format={spec.format})의 채점기는 아직 구현되지 않았습니다.",
    )


__all__ = ["GradingResult", "grade"]
