"""채점기 + /submissions 엔드포인트 통합 테스트."""

import json

import pytest
from fastapi.testclient import TestClient

from app.grading import grade
from app.main import app
from app.sandbox import SandboxResult
from app.schemas.problem import ExpectedOutput


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestScalarGrader:
    spec = ExpectedOutput(format="scalar", schema="int", tolerance=0.0, answer=5)

    def test_correct_answer(self) -> None:
        r = grade(self.spec, SandboxResult(stdout="5\n"))
        assert r.passed and r.score == 1.0

    def test_wrong_answer(self) -> None:
        r = grade(self.spec, SandboxResult(stdout="3\n"))
        assert not r.passed
        assert "기대값과 다릅니다" in r.feedback

    def test_empty_output(self) -> None:
        r = grade(self.spec, SandboxResult(stdout=""))
        assert r.error_code == "OUTPUT_PARSE"

    def test_unparseable_output(self) -> None:
        r = grade(self.spec, SandboxResult(stdout="not a number\n"))
        assert r.error_code == "OUTPUT_PARSE"

    def test_last_line_is_evaluated(self) -> None:
        # 디버그 출력 후 마지막에 답을 print 해도 통과
        r = grade(self.spec, SandboxResult(stdout="debug info\nshape: (10,4)\n5\n"))
        assert r.passed

    def test_tolerance_within(self) -> None:
        spec = ExpectedOutput(format="scalar", schema="float", tolerance=0.05, answer=0.85)
        r = grade(spec, SandboxResult(stdout="0.86\n"))
        assert r.passed

    def test_tolerance_exceeded(self) -> None:
        spec = ExpectedOutput(format="scalar", schema="float", tolerance=0.01, answer=0.85)
        r = grade(spec, SandboxResult(stdout="0.95\n"))
        assert not r.passed

    def test_propagates_sandbox_error(self) -> None:
        r = grade(self.spec, SandboxResult(error_code="TIMEOUT", stderr="too long"))
        assert not r.passed
        assert r.error_code == "TIMEOUT"
        assert "초과" in r.feedback


class TestSubmissionsEndpoint:
    def test_correct_solution_passes(self, client: TestClient) -> None:
        """샘플 문제 pp1-missing-001 의 정답 코드를 그대로 제출 → 통과."""
        problem_json = json.loads(
            (
                __import__("pathlib").Path(__file__).resolve().parent.parent.parent
                / "content"
                / "problems"
                / "practical_1"
                / "pp1-missing-001.json"
            ).read_text(encoding="utf-8")
        )
        response = client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": problem_json["solution_code"]},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["passed"] is True
        assert body["error_code"] is None

    def test_wrong_answer(self, client: TestClient) -> None:
        response = client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": "print(99)"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["passed"] is False
        assert body["error_code"] is None  # 채점 자체는 정상

    def test_forbidden_pattern(self, client: TestClient) -> None:
        response = client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": "import os\nprint(len(os.listdir('.')))"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["error_code"] == "FORBIDDEN_PATTERN"

    def test_runtime_error(self, client: TestClient) -> None:
        response = client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": "print(1/0)"},
        )
        body = response.json()
        assert body["error_code"] == "RUNTIME_ERROR"

    def test_unknown_problem_404(self, client: TestClient) -> None:
        response = client.post(
            "/submissions",
            json={"problem_id": "does-not-exist", "code": "print(1)"},
        )
        assert response.status_code == 404
