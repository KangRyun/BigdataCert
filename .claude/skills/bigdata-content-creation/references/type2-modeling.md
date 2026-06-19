# 작업형 2: 분류/회귀 모델링

scikit-learn 기반 End-to-End ML 파이프라인. 가장 배점 높은 유형.

## 출제 패턴

| 패턴 | 데이터 예시 | 평가 지표 |
|------|-----------|----------|
| 이진 분류 | 이탈/구매/생존 예측 | ROC-AUC |
| 다중 분류 | 카테고리 분류 | macro F1 |
| 회귀 | 가격·수요 예측 | RMSE |
| 불균형 분류 | 사기 탐지 | F1, AUC-PR |

## 출력 형식

제출 파일은 항상 CSV. 시험 형식 그대로:

```python
# 분류
pred = model.predict_proba(X_test)[:, 1]
pd.DataFrame({"pred": pred}).to_csv("pred.csv", index=False)

# 회귀
pred = model.predict(X_test)
pd.DataFrame({"pred": pred}).to_csv("pred.csv", index=False)
```

## 정답 코드 템플릿

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

train = pd.read_csv("train.csv")
test = pd.read_csv("test.csv")

# 전처리
y = train["target"]
X = train.drop(columns=["target", "id"])
X_test = test.drop(columns=["id"])

# 범주형 인코딩
X = pd.get_dummies(X, drop_first=True)
X_test = pd.get_dummies(X_test, drop_first=True)
X, X_test = X.align(X_test, join="left", axis=1, fill_value=0)

# 결측치
X = X.fillna(X.median(numeric_only=True))
X_test = X_test.fillna(X.median(numeric_only=True))

# 검증
X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_tr, y_tr)

val_pred = model.predict_proba(X_val)[:, 1]
print("val ROC-AUC:", roc_auc_score(y_val, val_pred))

# 제출
model.fit(X, y)
pred = model.predict_proba(X_test)[:, 1]
pd.DataFrame({"pred": pred}).to_csv("pred.csv", index=False)
```

## expected_output 패턴

```json
{
  "format": "csv",
  "schema": "pred",
  "metric": "roc_auc",
  "tolerance": 0.02
}
```

> tolerance는 채점기가 정답코드의 점수 ± tolerance 범위 내 학생 점수를 만점 처리할 때 사용. 분류는 0.02 ~ 0.05, 회귀는 RMSE 기준 ± 5%.

## 흔한 함정

- **train/test 컬럼 불일치**: get_dummies 후 align 누락 → 학습/예측 컬럼 mismatch. `X.align(X_test, join="left", axis=1, fill_value=0)` 필수
- **데이터 누수**: train의 median으로 test도 채워야 함. test에서 별도 median 계산 금지
- **타겟 인코딩 누수**: 교차검증 fold 내에서만 인코딩 수행
- **확률 vs 클래스**: ROC-AUC는 `predict_proba`, F1은 `predict`. 평가 지표에 맞춰 출력
- **시험 환경 메모리 한도**: GridSearchCV는 신중히. 작은 n_iter RandomizedSearchCV 권장
