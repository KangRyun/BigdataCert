"""CSV 산출물 채점 — 작업형 2.

학습자 코드가 pred.csv 같은 결과 파일을 만들면 SandboxResult.artifacts 에서 꺼내
truth_paths['truth.csv'] 와 비교해 metric(ROC-AUC, F1, RMSE)을 계산한다.

기본 산출물명은 'pred.csv'. expected_output.schema_ 가 컬럼명 (단일 컬럼만 지원).
"""

import io
from pathlib import Path

import numpy as np
import pandas as pd

from app.grading.base import GradingResult
from app.sandbox import SandboxResult
from app.schemas.problem import ExpectedOutput

_DEFAULT_ARTIFACT = "pred.csv"
_TRUTH_COLUMN = "target"


def _ok(passed: bool, score: float, metric: str, feedback: str) -> GradingResult:
    return GradingResult(passed=passed, score=score, metric_name=metric, feedback=feedback)


def _fail(metric: str, code: str, feedback: str) -> GradingResult:
    return GradingResult(
        passed=False, score=0.0, metric_name=metric, error_code=code, feedback=feedback
    )


def grade_csv(
    spec: ExpectedOutput, result: SandboxResult, truth_paths: dict[str, Path]
) -> GradingResult:
    metric = spec.metric or "unknown"

    text = result.artifacts.get(_DEFAULT_ARTIFACT)
    if text is None:
        return _fail(
            metric,
            "MISSING_ARTIFACT",
            f"제출 파일 {_DEFAULT_ARTIFACT} 을 찾을 수 없습니다. 코드 마지막에 pred.csv 로 저장하세요.",
        )

    truth_path = truth_paths.get("truth.csv")
    if not truth_path:
        return _fail(
            metric, "SPEC_MISSING_TRUTH", "문제 정의에 정답 라벨(truth.csv)이 없습니다."
        )

    expected_col = spec.schema_ if isinstance(spec.schema_, str) else "pred"

    try:
        pred = pd.read_csv(io.StringIO(text))
    except Exception as exc:
        return _fail(metric, "OUTPUT_PARSE", f"pred.csv 파싱 실패: {exc}")

    if list(pred.columns) != [expected_col]:
        return _fail(
            metric,
            "SHAPE_MISMATCH",
            f"컬럼명이 다릅니다. 기대: [{expected_col}], 제출: {list(pred.columns)}",
        )

    truth = pd.read_csv(truth_path)
    if _TRUTH_COLUMN not in truth.columns:
        return _fail(metric, "SPEC_INVALID_TRUTH", f"truth.csv 에 {_TRUTH_COLUMN} 컬럼이 없습니다.")

    if len(pred) != len(truth):
        return _fail(
            metric,
            "SHAPE_MISMATCH",
            f"행 수가 다릅니다. 기대: {len(truth)}, 제출: {len(pred)}",
        )

    baseline = spec.baseline if spec.baseline is not None else 0.0
    tol = spec.tolerance or 0.0
    y_true = truth[_TRUTH_COLUMN].to_numpy()
    y_pred = pred[expected_col].to_numpy()

    try:
        if metric == "roc_auc":
            from sklearn.metrics import roc_auc_score

            score = float(roc_auc_score(y_true, y_pred))
            passed = score >= baseline - tol
            cmp = f"≥ {baseline:.4f} - {tol}"
        elif metric == "f1_macro":
            from sklearn.metrics import f1_score

            score = float(f1_score(y_true, y_pred.astype(int), average="macro"))
            passed = score >= baseline - tol
            cmp = f"≥ {baseline:.4f} - {tol}"
        elif metric == "accuracy":
            score = float(np.mean(y_true == y_pred.astype(int)))
            passed = score >= baseline - tol
            cmp = f"≥ {baseline:.4f} - {tol}"
        elif metric == "rmse":
            score = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
            passed = score <= baseline + tol
            cmp = f"≤ {baseline:.4f} + {tol}"
        else:
            return _fail(metric, "UNSUPPORTED_METRIC", f"지원하지 않는 metric: {metric}")
    except Exception as exc:
        return _fail(metric, "METRIC_ERROR", f"채점 중 오류: {exc}")

    verdict = "통과" if passed else "미달"
    return _ok(
        passed,
        score,
        metric,
        f"{metric}: {score:.4f} (기준 {cmp}) → {verdict}",
    )
