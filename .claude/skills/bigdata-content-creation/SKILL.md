---
name: bigdata-content-creation
description: "빅데이터분석기사 실기·필기 문제·해설·정답코드 제작 가이드. 작업형1(전처리/요약), 작업형2(분류/회귀), 작업형3(통계분석), 필기 객관식 4가지 유형 모두 다룬다. content-author 에이전트가 빅분기 콘텐츠를 만들 때 반드시 이 스킬을 사용. '문제 만들기', '문제 추가', '해설 작성', '정답 코드', '난이도 조정', '오답 패턴' 같은 요청에도 이 스킬을 트리거."
---

# 빅분기 콘텐츠 제작 가이드

빅데이터분석기사 실기·필기 시험을 대비하는 학습 콘텐츠를 만들 때 따르는 절차와 형식 표준.

## 시험 유형 개요

| 유형 | 라이브러리 | 출력 형식 | 평가 방식 |
|------|----------|----------|----------|
| 작업형 1 | pandas, numpy | 스칼라/딕셔너리/리스트 | 정답 일치 (허용 오차 사용 가능) |
| 작업형 2 | pandas, scikit-learn | CSV (예측값) | 모델 성능 지표 (ROC-AUC, F1, RMSE 등) |
| 작업형 3 | scipy, statsmodels | 스칼라/딕셔너리 | p-value, 검정통계량 일치 |
| 필기 | (이론) | 4지선다 | 정답 번호 |

## 문제 JSON 스키마 (단일 진실 원천)

모든 문제는 다음 스키마를 따른다:

```json
{
  "problem_id": "{exam_type}-{topic_slug}-{NNN}",
  "exam_type": "practical_1 | practical_2 | practical_3 | written",
  "title": "문제 제목 (한국어)",
  "difficulty": "easy | medium | hard",
  "topic_tags": ["preprocessing", "classification", ...],
  "description": "마크다운 형식 문제 설명",
  "sample_data": {
    "train.csv": "...",      // 인라인 또는 경로
    "test.csv": "..."
  },
  "expected_output": {
    "format": "scalar | csv | dict | choice",
    "schema": "컬럼명 또는 키 구조",
    "tolerance": 0.02,        // 부동소수 비교 시
    "metric": "roc_auc | rmse | accuracy | exact"  // 작업형2 한정
  },
  "hints": ["단계1", "단계2", "단계3"],   // 3단계 점진 공개
  "solution_code": "실행 가능한 Python 코드 전문",
  "explanation": "마크다운 해설 — 왜 정답인가 + 흔한 오답"
}
```

> 이 스키마는 backend-engineer의 채점기와 frontend-engineer의 렌더러가 함께 의존하는 계약. 변경 시 세 에이전트 모두 합의 필요.

## 유형별 작성 절차

각 유형의 상세 작성 절차·예시는 references에 분리되어 있다:

- 작업형 1 → `references/type1-preprocessing.md`
- 작업형 2 → `references/type2-modeling.md`
- 작업형 3 → `references/type3-statistics.md`
- 필기 이론 → `references/written-theory.md`

## 공통 작성 원칙

### 정답 코드 작성 원칙

1. **자기완결**: 첫 줄부터 마지막 줄까지 그대로 실행 가능. import → 데이터 로딩 → 처리 → 출력 순.
2. **결정성**: 모델은 `random_state=42` 고정. shuffle, split도 동일 시드.
3. **출력 일치**: 기대 출력 형식(스칼라/CSV/딕셔너리)에 정확히 맞춤. 작업형2는 `pred.to_csv("pred.csv", index=False)` 같은 명시적 저장.
4. **표준 라이브러리만**: pandas, numpy, sklearn, scipy, statsmodels, matplotlib. 비표준 패키지(xgboost, lightgbm) 사용 시 별도 표시.

### 난이도 가이드

| 난이도 | 작업형 1 기준 | 작업형 2 기준 | 작업형 3 기준 |
|--------|--------------|--------------|--------------|
| easy | groupby/agg 1단 | 전처리 최소 + 1개 모델 | t-검정/카이제곱 단발 |
| medium | 결측치+이상치+파생변수 | 전처리 + 모델 비교 + 평가 | ANOVA, 회귀분석 |
| hard | 복합 그룹 집계 + 시계열 | 파이프라인 + 하이퍼파라미터 튜닝 | 다중공선성·잔차 진단 |

### 힌트 3단계 설계

- **hint1**: 어디서부터 시작할지 (예: "데이터를 먼저 살펴보세요. info()와 isna().sum()을 사용.")
- **hint2**: 핵심 접근 방향 (예: "범주형은 원-핫 인코딩으로, 수치형은 표준화로 처리해보세요.")
- **hint3**: 거의 정답 직전 (예: "RandomForestClassifier(n_estimators=200, random_state=42)으로 학습 후 predict_proba 사용.")

### 해설 구조

```markdown
## 풀이 접근
1. 문제 인식: 무엇을 묻는가
2. 데이터 탐색: 어떤 특징이 보이는가
3. 전처리 전략: 어떤 변환을 선택했고 왜
4. 모델·검정 선택: 왜 이 방법인가
5. 결과 해석: 점수가 의미하는 바

## 흔한 오답
- (오답 패턴 A): 왜 잘못됐는가
- (오답 패턴 B): 어떤 결과가 나오는가
```

## 콘텐츠 디렉토리 구조

```
content/
├── problems/
│   ├── practical_1/
│   │   ├── pp1-missing-001.json
│   │   └── ...
│   ├── practical_2/
│   ├── practical_3/
│   └── written/
└── data/
    └── {problem_id}/
        ├── train.csv
        └── test.csv
```

## 검증 체크리스트 (작성 직후 수행)

문제 1개 작성을 끝낼 때마다:

- [ ] `solution_code`가 단독 실행 가능 (의존성·경로 포함)
- [ ] 실행 결과가 `expected_output`과 일치 (작업형2는 tolerance 내)
- [ ] `random_state`/seed 고정으로 재현성 확보
- [ ] hint 3단계가 점진적으로 정보 공개
- [ ] 해설에 흔한 오답 패턴 1개 이상 포함
- [ ] 기존 문제와 주제·데이터셋 중복 없음

## QA 회귀 검증

content-author는 backend-engineer가 채점기를 갖춘 직후, 자신의 모든 `solution_code`를 채점기에 통과시키는 회귀 스크립트를 qa-integration과 함께 운영한다. 채점 정합성 검증은 `references/grading-contract.md` 참조.
