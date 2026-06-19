"""csv/dict/choice 그레이더 + 보안 회귀 통합 테스트."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content"


def _load(rel: str) -> dict:
    return json.loads((CONTENT_DIR / "problems" / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


_ALL_PROBLEMS = [
    # 작업형 1
    ("practical_1/pp1-missing-001.json", "pp1-missing-001"),
    ("practical_1/pp1-iqr-001.json", "pp1-iqr-001"),
    ("practical_1/pp1-groupby-001.json", "pp1-groupby-001"),
    ("practical_1/pp1-quantile-001.json", "pp1-quantile-001"),
    # 작업형 2
    ("practical_2/pp2-churn-001.json", "pp2-churn-001"),
    ("practical_2/pp2-housing-001.json", "pp2-housing-001"),
    ("practical_2/pp2-multi-001.json", "pp2-multi-001"),
    ("practical_2/pp2-imbalanced-001.json", "pp2-imbalanced-001"),
    # 작업형 3
    ("practical_3/pp3-ttest-001.json", "pp3-ttest-001"),
    ("practical_3/pp3-chi2-001.json", "pp3-chi2-001"),
    ("practical_3/pp3-anova-001.json", "pp3-anova-001"),
    ("practical_3/pp3-corr-001.json", "pp3-corr-001"),
    # 필기
    ("written/w-ensemble-001.json", "w-ensemble-001"),
    ("written/w-eda-001.json", "w-eda-001"),
    ("written/w-metrics-001.json", "w-metrics-001"),
    ("written/w-pvalue-001.json", "w-pvalue-001"),
]


# ---------- 보안 회귀 ----------

class TestPublicLeakage:
    """학습자에게 노출되는 응답에는 정답 단서가 절대 들어가서는 안 된다."""

    @pytest.mark.parametrize("rel,pid", _ALL_PROBLEMS)
    def test_no_answer_leak(self, client: TestClient, rel: str, pid: str) -> None:
        response = client.get(f"/problems/{pid}")
        assert response.status_code == 200, response.text
        body = response.json()
        eo = body["expected_output"]
        # 절대 노출 금지 필드
        assert "answer" not in eo, f"answer 누출 in {pid}"
        assert "baseline" not in eo, f"baseline 누출 in {pid}"
        # 정답·해설·truth_data 누출 금지
        for forbidden in ("solution_code", "explanation", "truth_data"):
            assert forbidden not in body, f"{forbidden} 누출 in {pid}"
        # 공개 필드는 그대로
        assert "format" in eo
        assert "tolerance" in eo


# ---------- 형식별 정답 코드 → 채점 통과 ----------

class TestSolutionsPassGrader:
    @pytest.mark.parametrize("rel,pid", _ALL_PROBLEMS)
    def test_solution_code_passes(self, client: TestClient, rel: str, pid: str) -> None:
        problem = _load(rel)
        response = client.post(
            "/submissions",
            json={"problem_id": pid, "code": problem["solution_code"]},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["passed"] is True, f"{pid} 정답 코드가 채점기를 통과하지 못함: {body}"
        assert body["error_code"] is None


# ---------- csv 채점기 오류 경로 ----------

class TestCsvGraderErrors:
    def test_missing_pred_csv(self, client: TestClient) -> None:
        # pred.csv 를 만들지 않는 코드
        code = "import pandas as pd\nprint('no submission')\n"
        r = client.post("/submissions", json={"problem_id": "pp2-churn-001", "code": code})
        body = r.json()
        assert body["error_code"] == "MISSING_ARTIFACT"

    def test_wrong_column_name(self, client: TestClient) -> None:
        code = (
            "import pandas as pd\n"
            "test = pd.read_csv('test.csv')\n"
            "pd.DataFrame({'prediction': [0.5]*len(test)}).to_csv('pred.csv', index=False)\n"
        )
        body = client.post("/submissions", json={"problem_id": "pp2-churn-001", "code": code}).json()
        assert body["error_code"] == "SHAPE_MISMATCH"


# ---------- dict 채점기 오류 경로 ----------

class TestDictGraderErrors:
    def test_missing_key(self, client: TestClient) -> None:
        code = "print({'t_statistic': 4.6455})\n"
        body = client.post("/submissions", json={"problem_id": "pp3-ttest-001", "code": code}).json()
        assert body["passed"] is False
        assert "p_value" in body["feedback"]

    def test_not_dict(self, client: TestClient) -> None:
        code = "print(4.6455)\n"
        body = client.post("/submissions", json={"problem_id": "pp3-ttest-001", "code": code}).json()
        assert body["error_code"] == "OUTPUT_PARSE"


# ---------- choice 채점기 오류 경로 ----------

class TestChoiceGraderErrors:
    def test_wrong_choice(self, client: TestClient) -> None:
        body = client.post("/submissions", json={"problem_id": "w-ensemble-001", "code": "print(1)"}).json()
        assert body["passed"] is False
        assert "오답" in body["feedback"]

    def test_non_integer_output(self, client: TestClient) -> None:
        body = client.post("/submissions", json={"problem_id": "w-ensemble-001", "code": "print('two')"}).json()
        assert body["error_code"] == "OUTPUT_PARSE"
