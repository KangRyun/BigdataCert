"""Google OAuth (POST /auth/google) 통합 테스트.

실제 Google 호출 없이 _verify_google_id_token 만 monkeypatch.
"""

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.config import settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def configure_google(monkeypatch):
    """settings.google_client_id 를 임시값으로. 실제 verify 호출은 monkeypatch."""
    monkeypatch.setattr(settings, "google_client_id", "test-client-id.apps.googleusercontent.com")


def mock_verify(returns: dict):
    """_verify_google_id_token 을 가짜로 교체. returns 는 ID token payload."""
    def _fn(_token: str) -> dict:
        return returns
    return _fn


class TestGoogleAuthHappyPath:
    def test_new_user_signup(self, client: TestClient, configure_google, monkeypatch) -> None:
        monkeypatch.setattr(
            auth_api,
            "_verify_google_id_token",
            mock_verify({
                "sub": "google-sub-001",
                "email": "newgoogle@example.com",
                "email_verified": True,
                "name": "Google New",
            }),
        )
        r = client.post("/auth/google", json={"id_token": "x" * 50})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["access_token"]
        assert body["user"]["email"] == "newgoogle@example.com"
        assert body["user"]["display_name"] == "Google New"

    def test_returning_user_by_sub(
        self, client: TestClient, configure_google, monkeypatch
    ) -> None:
        payload = {
            "sub": "google-sub-002",
            "email": "returning@example.com",
            "email_verified": True,
            "name": "Returning",
        }
        monkeypatch.setattr(auth_api, "_verify_google_id_token", mock_verify(payload))
        first = client.post("/auth/google", json={"id_token": "x" * 50}).json()
        second = client.post("/auth/google", json={"id_token": "x" * 50}).json()
        # 같은 user.id 가 발급되어야 함
        assert first["user"]["id"] == second["user"]["id"]

    def test_link_existing_password_account_by_email(
        self, client: TestClient, configure_google, monkeypatch
    ) -> None:
        # 1) 이메일/비번으로 먼저 가입
        reg = client.post(
            "/auth/register",
            json={
                "email": "shared@example.com",
                "password": "originalpass",
                "display_name": "Original",
            },
        )
        original_id = reg.json()["user"]["id"]

        # 2) 같은 이메일로 Google 로그인 시도 → 기존 계정에 linking
        monkeypatch.setattr(
            auth_api,
            "_verify_google_id_token",
            mock_verify({
                "sub": "google-sub-003",
                "email": "shared@example.com",
                "email_verified": True,
                "name": "Original Google",
            }),
        )
        r = client.post("/auth/google", json={"id_token": "x" * 50})
        assert r.status_code == 200
        assert r.json()["user"]["id"] == original_id
        # display_name 은 기존값 유지 (덮어쓰지 않음)
        assert r.json()["user"]["display_name"] == "Original"


class TestGoogleAuthRejections:
    def test_google_not_configured(
        self, client: TestClient, monkeypatch
    ) -> None:
        monkeypatch.setattr(settings, "google_client_id", None)
        r = client.post("/auth/google", json={"id_token": "x" * 50})
        assert r.status_code == 503
        assert r.json()["detail"]["error_code"] == "GOOGLE_NOT_CONFIGURED"

    def test_invalid_token(
        self, client: TestClient, configure_google, monkeypatch
    ) -> None:
        def bad(_t):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail={"error_code": "INVALID_GOOGLE_TOKEN"})
        monkeypatch.setattr(auth_api, "_verify_google_id_token", bad)
        r = client.post("/auth/google", json={"id_token": "x" * 50})
        assert r.status_code == 401
        assert r.json()["detail"]["error_code"] == "INVALID_GOOGLE_TOKEN"

    def test_unverified_email_rejected(
        self, client: TestClient, configure_google, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            auth_api,
            "_verify_google_id_token",
            mock_verify({
                "sub": "google-sub-004",
                "email": "unverified@example.com",
                "email_verified": False,
                "name": "Unverified",
            }),
        )
        r = client.post("/auth/google", json={"id_token": "x" * 50})
        assert r.status_code == 400
        assert r.json()["detail"]["error_code"] == "GOOGLE_EMAIL_UNVERIFIED"

    def test_missing_sub_or_email(
        self, client: TestClient, configure_google, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            auth_api,
            "_verify_google_id_token",
            mock_verify({"sub": "x", "email_verified": True}),  # email 누락
        )
        r = client.post("/auth/google", json={"id_token": "x" * 50})
        assert r.status_code == 400
        assert r.json()["detail"]["error_code"] == "INVALID_GOOGLE_PAYLOAD"
