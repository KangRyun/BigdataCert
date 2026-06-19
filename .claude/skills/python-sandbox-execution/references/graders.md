# 채점기 구현 (format 별)

`bigdata-content-creation/references/grading-contract.md`와 짝을 이루는 백엔드 측 구현 가이드. 콘텐츠 계약의 모든 format을 빠짐없이 구현한다.

## 공통 인터페이스

```python
from pydantic import BaseModel
from pathlib import Path

class ExpectedOutput(BaseModel):
    format: Literal["scalar", "csv", "dict", "choice"]
    schema_: dict | str | None = None     # format별 의미 다름
    tolerance: float = 0.0
    metric: str | None = None
    baseline: float | None = None         # csv format 전용 (정답코드 점수)
    truth_path: Path | None = None        # csv format 전용 (정답 라벨)
    answer: int | float | str | dict | None = None  # 정답 값 또는 라벨

class SandboxResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    artifacts: dict[str, Path] = {}    # 생성된 파일들 (예: pred.csv)
    error_code: str | None = None

class GradingResult(BaseModel):
    passed: bool
    score: float
    metric_name: str
    feedback: str
    error_code: str | None = None
```

## scalar (작업형 1, 작업형 3 일부)

stdout의 마지막 줄을 파싱.

```python
def grade_scalar(spec, result):
    try:
        line = result.stdout.strip().splitlines()[-1]
        value = float(line)
    except (ValueError, IndexError):
        return GradingResult(
            passed=False, score=0.0, metric_name="exact",
            error_code="OUTPUT_PARSE",
            feedback="출력의 마지막 줄에 숫자값을 print 하세요."
        )

    if math.isclose(value, spec.answer, rel_tol=spec.tolerance, abs_tol=spec.tolerance):
        return GradingResult(passed=True, score=1.0, metric_name="exact", feedback="정답입니다.")
    return GradingResult(
        passed=False, score=0.0, metric_name="exact",
        feedback=f"기대값과 다릅니다. (제출: {value}, 기댓값과 허용오차: {spec.answer} ± {spec.tolerance})"
    )
```

## csv (작업형 2)

작업공간에서 `pred.csv`를 찾아 정답 라벨과 비교.

```python
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, mean_squared_error

def grade_csv(spec, result):
    pred_path = result.artifacts.get("pred.csv")
    if not pred_path:
        return GradingResult(
            passed=False, score=0.0, metric_name=spec.metric,
            error_code="MISSING_ARTIFACT",
            feedback="pred.csv 파일을 생성하지 못했습니다."
        )

    pred = pd.read_csv(pred_path)
    if list(pred.columns) != [spec.schema_]:
        return GradingResult(
            passed=False, score=0.0, metric_name=spec.metric,
            error_code="SHAPE_MISMATCH",
            feedback=f"컬럼명이 다릅니다. 기대: [{spec.schema_}], 제출: {list(pred.columns)}"
        )

    truth = pd.read_csv(spec.truth_path)
    if spec.metric == "roc_auc":
        score = roc_auc_score(truth["target"], pred[spec.schema_])
        passed = score >= spec.baseline - spec.tolerance
    elif spec.metric == "f1_macro":
        score = f1_score(truth["target"], pred[spec.schema_], average="macro")
        passed = score >= spec.baseline - spec.tolerance
    elif spec.metric == "rmse":
        score = np.sqrt(mean_squared_error(truth["target"], pred[spec.schema_]))
        passed = score <= spec.baseline + spec.tolerance
    else:
        raise NotImplementedError(spec.metric)

    return GradingResult(
        passed=passed, score=float(score), metric_name=spec.metric,
        feedback=f"{spec.metric}: {score:.4f} (기준 {spec.baseline:.4f}, 허용 ±{spec.tolerance})"
    )
```

## dict (작업형 3 다중 산출)

stdout 마지막 줄에 `repr(dict)` 형태로 출력된 결과를 안전 파싱.

```python
import ast

def grade_dict(spec, result):
    try:
        line = result.stdout.strip().splitlines()[-1]
        parsed = ast.literal_eval(line)
        assert isinstance(parsed, dict)
    except Exception:
        return GradingResult(
            passed=False, score=0.0, metric_name="dict",
            error_code="OUTPUT_PARSE",
            feedback="출력의 마지막 줄에 딕셔너리를 print 하세요. 예: {'p_value': 0.03}"
        )

    expected = spec.answer       # dict
    misses = []
    for key, expected_value in expected.items():
        if key not in parsed:
            misses.append(f"누락된 키: {key}")
            continue
        if not math.isclose(parsed[key], expected_value, rel_tol=spec.tolerance, abs_tol=spec.tolerance):
            misses.append(f"{key}: 제출 {parsed[key]} vs 기대 {expected_value}")

    if misses:
        return GradingResult(
            passed=False, score=0.0, metric_name="dict",
            feedback="다음 항목이 불일치합니다:\n" + "\n".join(misses)
        )
    return GradingResult(passed=True, score=1.0, metric_name="dict", feedback="정답입니다.")
```

## choice (필기)

```python
def grade_choice(spec, result):
    try:
        value = int(result.stdout.strip().splitlines()[-1])
    except Exception:
        return GradingResult(
            passed=False, score=0.0, metric_name="choice",
            error_code="OUTPUT_PARSE",
            feedback="정답 번호(1-4)를 print 하세요."
        )

    if value == spec.answer:
        return GradingResult(passed=True, score=1.0, metric_name="choice", feedback="정답입니다.")
    return GradingResult(
        passed=False, score=0.0, metric_name="choice",
        feedback=f"오답입니다. (정답: {spec.answer})"
    )
```

## 디스패치

```python
GRADERS = {
    "scalar": grade_scalar,
    "csv": grade_csv,
    "dict": grade_dict,
    "choice": grade_choice,
}

def grade(spec: ExpectedOutput, result: SandboxResult) -> GradingResult:
    if result.error_code:
        return GradingResult(
            passed=False, score=0.0, metric_name=spec.format,
            error_code=result.error_code, feedback=result.stderr[:500]
        )
    return GRADERS[spec.format](spec, result)
```
