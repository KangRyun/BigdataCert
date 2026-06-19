"""Smoke 테스트 — 핵심 엔드포인트가 200을 반환하는지만 확인.

추후 grading·auth가 추가되면 integration 테스트로 확장.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_list_problems_returns_array(client: TestClient) -> None:
    response = client.get("/problems")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_get_sample_problem(client: TestClient) -> None:
    """샘플 문제 1개가 정상 조회되어야 함."""
    response = client.get("/problems/pp1-missing-001")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["problem_id"] == "pp1-missing-001"
    assert body["exam_type"] == "practical_1"
    assert "description" in body
    assert "expected_output" in body
    # 정답·해설은 노출되지 않아야 함
    assert "solution_code" not in body
    assert "explanation" not in body


def test_get_unknown_problem_404(client: TestClient) -> None:
    response = client.get("/problems/does-not-exist")
    assert response.status_code == 404
