"""제출 영속화 + /me 엔드포인트 테스트."""

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


def _register_and_token(client: TestClient, email: str) -> str:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "secretpass", "display_name": email.split("@")[0]},
    )
    return r.json()["access_token"]


class TestPersistedSubmissions:
    def test_anonymous_submission_not_persisted(self, client: TestClient) -> None:
        # 비로그인 제출 — 결과는 받지만 /me 에는 안 잡힘
        problem = _load("practical_1/pp1-missing-001.json")
        r = client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": problem["solution_code"]},
        )
        assert r.status_code == 200
        assert r.json()["passed"] is True
        # 새 유저로 가입 → 본인 제출 목록은 비어 있어야 함
        token = _register_and_token(client, "anon-witness@example.com")
        me = client.get("/me/submissions", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json() == []

    def test_authenticated_submission_persisted(self, client: TestClient) -> None:
        token = _register_and_token(client, "eve@example.com")
        problem = _load("practical_1/pp1-missing-001.json")
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": problem["solution_code"]},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["passed"] is True

        me = client.get("/me/submissions", headers=headers)
        assert me.status_code == 200
        items = me.json()
        assert len(items) == 1
        assert items[0]["problem_id"] == "pp1-missing-001"
        assert items[0]["passed"] is True
        assert items[0]["score"] == 1.0

    def test_failed_submission_also_persisted(self, client: TestClient) -> None:
        token = _register_and_token(client, "frank@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": "print(99)"},
            headers=headers,
        )
        items = client.get("/me/submissions", headers=headers).json()
        assert len(items) == 1
        assert items[0]["passed"] is False

    def test_other_users_submissions_invisible(self, client: TestClient) -> None:
        token_a = _register_and_token(client, "user-a@example.com")
        token_b = _register_and_token(client, "user-b@example.com")
        problem = _load("practical_1/pp1-missing-001.json")
        client.post(
            "/submissions",
            json={"problem_id": "pp1-missing-001", "code": problem["solution_code"]},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        items_b = client.get(
            "/me/submissions", headers={"Authorization": f"Bearer {token_b}"}
        ).json()
        assert items_b == []


class TestProgressEndpoint:
    def test_empty_progress(self, client: TestClient) -> None:
        token = _register_and_token(client, "george@example.com")
        r = client.get("/me/progress", headers={"Authorization": f"Bearer {token}"})
        body = r.json()
        for key in ("practical_1", "practical_2", "practical_3", "written"):
            assert body[key] == {"attempts": 0, "passed_attempts": 0, "solved": 0}

    def test_progress_aggregates_correctly(self, client: TestClient) -> None:
        token = _register_and_token(client, "henry@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # pp1 정답 + pp1 오답 → 시도 2, 통과 1, 해결 1개
        sol = _load("practical_1/pp1-missing-001.json")["solution_code"]
        client.post("/submissions", json={"problem_id": "pp1-missing-001", "code": sol}, headers=headers)
        client.post("/submissions", json={"problem_id": "pp1-missing-001", "code": "print(0)"}, headers=headers)
        # 필기 정답
        wsol = _load("written/w-ensemble-001.json")["solution_code"]
        client.post("/submissions", json={"problem_id": "w-ensemble-001", "code": wsol}, headers=headers)

        body = client.get("/me/progress", headers=headers).json()
        assert body["practical_1"] == {"attempts": 2, "passed_attempts": 1, "solved": 1}
        assert body["written"] == {"attempts": 1, "passed_attempts": 1, "solved": 1}
        assert body["practical_2"]["attempts"] == 0
        assert body["practical_3"]["attempts"] == 0


class TestMeRequiresAuth:
    def test_submissions_requires_auth(self, client: TestClient) -> None:
        r = client.get("/me/submissions")
        assert r.status_code == 401

    def test_progress_requires_auth(self, client: TestClient) -> None:
        r = client.get("/me/progress")
        assert r.status_code == 401
