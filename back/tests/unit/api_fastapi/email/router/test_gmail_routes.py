import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_email_handlers
from src.api_fastapi.main import create_app


class _FakeEmailHandlers:
    def get_gmail_status(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "authorized": True, "user_id": user_id}

    def handle_gmail_authorize(self, redirect_url: str | None = None) -> dict:
        return {"status": "ok", "auth_url": "https://example.com/oauth", "redirect_url": redirect_url}

    def get_gmail_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict:
        return {"status": "ok", "auth_url": "https://example.com/start", "redirect_url": redirect_url, "user_id": user_id}

    def revoke_gmail(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "message": "revoked", "user_id": user_id}

    def get_gmail_profile(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "email": "user@example.com", "user_id": user_id}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_email_handlers] = lambda: _FakeEmailHandlers()
    return TestClient(app)


def test_gmail_status_route_uses_query_user_id():
    client = _client()

    response = client.get("/api/gmail/status?user_id=u-1")

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-1"


def test_gmail_authorize_route_returns_auth_url():
    client = _client()

    response = client.get("/api/gmail/authorize?redirect_url=https://front/settings")

    assert response.status_code == 200
    assert response.json()["auth_url"] == "https://example.com/oauth"


def test_gmail_oauth_start_route_supports_user_context():
    client = _client()

    response = client.get("/api/gmail/oauth/start?redirect_url=https://front/settings&user_id=u-2")

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-2"


def test_gmail_revoke_route_returns_message():
    client = _client()

    response = client.get("/api/gmail/revoke?user_id=u-3")

    assert response.status_code == 200
    assert response.json()["message"] == "revoked"


def test_gmail_profile_route_returns_profile_payload():
    client = _client()

    response = client.get("/api/gmail/profile?user_id=u-4")

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
