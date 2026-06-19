# 채점 계약 (Grading Contract)

content-author ↔ backend-engineer 사이의 단일 진실 원천(SSOT). 모든 문제는 이 계약을 따라야 채점이 결정적으로 통과한다.

## 채점 흐름

```
사용자 코드 제출
  → backend.sandbox.run(user_code, sample_data)
  → 실행 결과 캡처 (stdout 또는 pred.csv)
  → backend.grading.grade(result, expected_output)
  → 점수 + 통과 여부 + 상세 피드백 반환
```

## expected_output.format 별 채점 로직

### `scalar`
```python
def grade_scalar(result, expected):
    parsed = float(result.strip())
    return math.isclose(parsed, expected.value, rel_tol=expected.tolerance)
```

### `csv`
```python
def grade_csv(pred_csv_path, expected):
    pred = pd.read_csv(pred_csv_path)
    assert list(pred.columns) == [expected.schema]   # 컬럼 일치
    truth = pd.read_csv(expected.truth_path)
    if expected.metric == "roc_auc":
        score = roc_auc_score(truth["target"], pred[expected.schema])
        return score >= expected.baseline - expected.tolerance
    elif expected.metric == "rmse":
        rmse = np.sqrt(((truth["target"] - pred[expected.schema]) ** 2).mean())
        return rmse <= expected.baseline + expected.tolerance
```

### `dict`
```python
def grade_dict(result_dict, expected):
    for key, expected_value in expected.schema.items():
        if key not in result_dict:
            return False
        if not math.isclose(result_dict[key], expected_value, rel_tol=expected.tolerance):
            return False
    return True
```

### `choice`
```python
def grade_choice(result, expected):
    return int(result) == expected.answer
```

## 콘텐츠 작성자가 보장할 사항

1. `solution_code`는 위 채점 로직을 통과한다 — 단독 실행 → 결과 캡처 → 채점기 통과 시 만점.
2. `expected_output.schema`는 채점기가 인식하는 키·컬럼명과 정확히 일치.
3. `tolerance`는 정답 코드의 random_state 변동성을 충분히 흡수 (분류 0.02, 회귀 5%, 통계 0.001).
4. 작업형 2의 `baseline`은 정답 코드 점수 그 자체. QA 회귀 스크립트가 검증.

## 백엔드 채점기 구현자가 보장할 사항

1. 모든 `format` 타입을 빠짐없이 구현 (scalar, csv, dict, choice).
2. 채점은 부수효과 없음 (멱등성).
3. 실패 사유를 구조화된 에러로 반환 (`{"error_code": "SHAPE_MISMATCH", "detail": ...}`).
4. 새 metric/format 추가 시 content-author에게 사전 통보.
