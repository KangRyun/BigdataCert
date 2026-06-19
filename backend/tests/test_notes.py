"""오답노트 CRUD 테스트."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str) -> dict[str, str]:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "secretpass", "display_name": email.split("@")[0]},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestNotesAuth:
    def test_list_requires_auth(self, client: TestClient) -> None:
        assert client.get("/me/notes").status_code == 401

    def test_get_requires_auth(self, client: TestClient) -> None:
        assert client.get("/me/notes/pp1-missing-001").status_code == 401

    def test_put_requires_auth(self, client: TestClient) -> None:
        assert client.put("/me/notes/pp1-missing-001", json={"content": "x"}).status_code == 401

    def test_delete_requires_auth(self, client: TestClient) -> None:
        assert client.delete("/me/notes/pp1-missing-001").status_code == 401


class TestNoteUpsert:
    def test_create_then_read(self, client: TestClient) -> None:
        h = _register(client, "ned@example.com")
        r = client.put(
            "/me/notes/pp1-missing-001",
            json={"content": "결측치는 isna().sum() 으로 먼저 본다."},
            headers=h,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["problem_id"] == "pp1-missing-001"
        assert body["content"].startswith("결측치는")

        r2 = client.get("/me/notes/pp1-missing-001", headers=h)
        assert r2.status_code == 200
        assert r2.json()["content"] == body["content"]

    def test_update_existing(self, client: TestClient) -> None:
        h = _register(client, "olive@example.com")
        client.put("/me/notes/pp1-missing-001", json={"content": "v1"}, headers=h)
        r = client.put("/me/notes/pp1-missing-001", json={"content": "v2"}, headers=h)
        assert r.status_code == 200
        assert r.json()["content"] == "v2"
        # 단 한 개의 노트만 존재
        items = client.get("/me/notes", headers=h).json()
        assert len(items) == 1
        assert items[0]["content"] == "v2"

    def test_unknown_problem_rejected(self, client: TestClient) -> None:
        h = _register(client, "paul@example.com")
        r = client.put(
            "/me/notes/does-not-exist",
            json={"content": "ghost note"},
            headers=h,
        )
        assert r.status_code == 404
        assert r.json()["detail"]["error_code"] == "PROBLEM_NOT_FOUND"

    def test_too_long_content_rejected(self, client: TestClient) -> None:
        h = _register(client, "quinn@example.com")
        r = client.put(
            "/me/notes/pp1-missing-001",
            json={"content": "x" * 30_000},
            headers=h,
        )
        assert r.status_code == 422


class TestNoteRead:
    def test_get_missing_returns_404(self, client: TestClient) -> None:
        h = _register(client, "rita@example.com")
        r = client.get("/me/notes/pp1-missing-001", headers=h)
        assert r.status_code == 404
        assert r.json()["detail"]["error_code"] == "NOTE_NOT_FOUND"

    def test_list_empty(self, client: TestClient) -> None:
        h = _register(client, "sam@example.com")
        assert client.get("/me/notes", headers=h).json() == []

    def test_list_ordered_by_updated_at_desc(self, client: TestClient) -> None:
        h = _register(client, "tina@example.com")
        client.put("/me/notes/pp1-missing-001", json={"content": "first"}, headers=h)
        client.put("/me/notes/pp2-churn-001", json={"content": "second"}, headers=h)
        # 첫 번째 노트를 다시 갱신 → 최신으로 올라와야 함
        client.put("/me/notes/pp1-missing-001", json={"content": "first-updated"}, headers=h)

        items = client.get("/me/notes", headers=h).json()
        assert [i["problem_id"] for i in items[:2]] == ["pp1-missing-001", "pp2-churn-001"]


class TestNoteDelete:
    def test_delete_existing(self, client: TestClient) -> None:
        h = _register(client, "ursula@example.com")
        client.put("/me/notes/pp1-missing-001", json={"content": "delete me"}, headers=h)
        r = client.delete("/me/notes/pp1-missing-001", headers=h)
        assert r.status_code == 204
        assert client.get("/me/notes/pp1-missing-001", headers=h).status_code == 404

    def test_delete_missing_is_idempotent(self, client: TestClient) -> None:
        h = _register(client, "victor@example.com")
        r = client.delete("/me/notes/pp1-missing-001", headers=h)
        assert r.status_code == 204


class TestNoteOwnerIsolation:
    def test_one_user_cannot_see_another_users_notes(self, client: TestClient) -> None:
        h_a = _register(client, "wanda@example.com")
        h_b = _register(client, "xander@example.com")
        client.put("/me/notes/pp1-missing-001", json={"content": "wanda only"}, headers=h_a)
        assert client.get("/me/notes/pp1-missing-001", headers=h_b).status_code == 404
        assert client.get("/me/notes", headers=h_b).json() == []
