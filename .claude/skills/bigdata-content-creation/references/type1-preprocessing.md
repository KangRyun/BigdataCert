# 작업형 1: 데이터 전처리·요약

pandas/numpy 단답형 문제. 데이터 정제·집계·정렬 능력을 검증한다.

## 출제 패턴

| 패턴 | 예시 | 출력 형식 |
|------|------|----------|
| 결측치 탐색·처리 | "결측치가 가장 많은 컬럼의 결측치 개수" | scalar (int) |
| 이상치 탐지 | "IQR 기준 이상치 개수" | scalar (int) |
| 집계 통계 | "범주별 평균/중앙값 차이" | scalar (float) |
| 정렬·필터 | "조건 만족하는 행 수" | scalar (int) |
| 시계열 | "특정 기간 합계" | scalar (float) |
| 파생 변수 | "수치 변환 후 분산" | scalar (float) |

## 정답 코드 템플릿

```python
import pandas as pd
import numpy as np

df = pd.read_csv("data.csv")

# 처리 로직
result = df.groupby("category")["value"].mean().max()

print(round(result, 2))   # 작업형1은 출력으로 답을 표현
```

## expected_output 패턴

```json
{
  "format": "scalar",
  "schema": "float",
  "tolerance": 0.01
}
```

## 흔한 함정

- **dtype 혼동**: `read_csv` 시 정수 컬럼이 float로 읽히는 경우 (NaN 때문). `dtype` 명시 또는 `astype` 변환
- **정렬 안정성**: `sort_values(by=[...])`에서 `kind="mergesort"` 사용 (시험 환경 일관성)
- **소수점 처리**: `round(result, 2)`로 명시. 표시 형식이 답에 영향
- **인덱스 보존**: `reset_index()`를 잊으면 groupby 결과가 Series가 되어 shape 불일치
