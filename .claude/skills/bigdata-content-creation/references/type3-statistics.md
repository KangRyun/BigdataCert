# 작업형 3: 통계 분석

scipy/statsmodels 기반 가설검정·회귀분석·ANOVA. 통계 개념의 적용을 검증한다.

## 출제 패턴

| 패턴 | 라이브러리 | 산출물 |
|------|----------|-------|
| 일/이표본 t-검정 | scipy.stats.ttest_ind | t-stat, p-value |
| 카이제곱 독립성 검정 | scipy.stats.chi2_contingency | chi2, p-value |
| 일원/이원 ANOVA | scipy.stats.f_oneway / statsmodels.formula.api.ols | F-stat, p-value |
| 상관 분석 | scipy.stats.pearsonr / spearmanr | r, p-value |
| 선형/로지스틱 회귀 | statsmodels.api.OLS / Logit | 계수, p-value, R² |
| 시계열 검정 | statsmodels.tsa.stattools.adfuller | ADF, p-value |

## 정답 코드 템플릿

```python
import pandas as pd
import scipy.stats as stats
import statsmodels.formula.api as smf

df = pd.read_csv("data.csv")

# 예: 두 집단 평균 차이 검정
group_a = df[df["group"] == "A"]["value"]
group_b = df[df["group"] == "B"]["value"]

t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)

print({"t_statistic": round(t_stat, 4), "p_value": round(p_value, 4)})
```

회귀 분석:

```python
model = smf.ols("y ~ x1 + x2 + C(category)", data=df).fit()
print({
    "r_squared": round(model.rsquared, 4),
    "coef_x1": round(model.params["x1"], 4),
    "p_x1": round(model.pvalues["x1"], 4)
})
```

## expected_output 패턴

```json
{
  "format": "dict",
  "schema": {"t_statistic": "float", "p_value": "float"},
  "tolerance": 0.001
}
```

## 흔한 함정

- **단/양측 검정 혼동**: `alternative="two-sided" | "less" | "greater"` 명시
- **등분산성 가정**: t-검정의 `equal_var` 기본값(True) 주의. 명시적으로 Welch 사용
- **scipy 버전 차이**: 일부 검정 결과 attribute name이 버전마다 다름 (statistic vs stat)
- **회귀 계수 키**: statsmodels는 카테고리 변수에 `C(cat)[T.value]` 형태로 이름 부여. 정확한 키 확인
- **유의수준 표기**: 시험은 α=0.05 기준이지만 문제에서 다른 값 지정할 수 있음
