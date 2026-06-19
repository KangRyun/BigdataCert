"""인증 흐름 통합 테스트."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestRegister:
    def test_register_returns_token_and_user(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={
                "email": "alice@example.com",
                "password": "supersecret",
                "display_name": "Alice",
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["user"]["email"] == "alice@example.com"
        assert body["user"]["display_name"] == "Alice"
        assert "id" in body["user"]
        # 비밀번호·해시는 절대 노출되지 않아야 함
        assert "password" not in body["user"]
        assert "password_hash" not in body["user"]

    def test_register_email_conflict(self, client: TestClient) -> None:
        payload = {
            "email": "bob@example.com",
            "password": "anotherpass",
            "display_name": "Bob",
        }
        client.post("/auth/register", json=payload)
        r2 = client.post("/auth/register", json=payload)
        assert r2.status_code == 409
        assert r2.json()["detail"]["error_code"] == "EMAIL_TAKEN"

    def test_short_password_rejected(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={"email": "x@y.com", "password": "short", "display_name": "X"},
        )
        assert r.status_code == 422

    def test_long_password_rejected(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={"email": "x@y.com", "password": "a" * 100, "display_name": "X"},
        )
        assert r.status_code == 422


class TestLogin:
    def _register(self, client: TestClient) -> tuple[str, str]:
        email = "cara@example.com"
        password = "carapassword"
        client.post(
            "/auth/register",
            json={"email": email, "password": password, "display_name": "Cara"},
        )
        return email, password

    def test_login_returns_token(self, client: TestClient) -> None:
        email, password = self._register(client)
        r = client.post("/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["access_token"]
        assert body["user"]["email"] == email

    def test_login_wrong_password(self, client: TestClient) -> None:
        email, _ = self._register(client)
        r = client.post("/auth/login", json={"email": email, "password": "wrong-pass"})
        assert r.status_code == 401
        assert r.json()["detail"]["error_code"] == "INVALID_CREDENTIALS"

    def test_login_unknown_email(self, client: TestClient) -> None:
        r = client.post(
            "/auth/login", json={"email": "ghost@example.com", "password": "nopassword"}
        )
        assert r.status_code == 401


class TestMeEndpoint:
    def test_me_requires_auth(self, client: TestClient) -> None:
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_returns_user_with_valid_token(self, client: TestClient) -> None:
        reg = client.post(
            "/auth/register",
            json={
                "email": "dan@example.com",
                "password": "danpassword",
                "display_name": "Dan",
            },
        )
        token = reg.json()["access_token"]
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert r.json()["email"] == "dan@example.com"

    def test_me_rejects_invalid_token(self, client: TestClient) -> None:
        r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert r.status_code == 401
