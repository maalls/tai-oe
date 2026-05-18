import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_auth_service, get_gmail_service
from src.api_fastapi.main import create_app


class _FakeGmailService:
    def get_status(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "authorized": True, "user_id": user_id}

    def authorize(self, redirect_url: str | None = None) -> dict:
        return {"status": "ok", "auth_url": "https://example.com/oauth", "redirect_url": redirect_url}

    def get_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict:
        return {"status": "ok", "auth_url": "https://example.com/start", "redirect_url": redirect_url, "user_id": user_id}

    def revoke(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "message": "revoked", "user_id": user_id}

    def get_profile(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "email": "user@example.com", "user_id": user_id}

    def oauth_callback(self, code: str, state: str | None = None) -> dict:
        _ = (code, state)
        return {"status": "ok", "redirect_url": "https://front/settings"}

    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False) -> dict:
        return {"status": "ok", "messages": [], "user_id": user_id, "max_results": max_results, "force": force}

    def classify_unclassified(self, user_id: str, limit: int = 200) -> dict:
        return {"status": "ok", "classified": 1, "user_id": user_id, "limit": limit}

    def get_message_body(self, message_id: str, user_id: str | None) -> dict:
        return {"status": "ok", "message": "body", "message_id": message_id, "user_id": user_id}

    def get_imap_status(self, user_id: str) -> dict:
        return {"status": "ok", "configured": True, "enabled": True, "connected": True, "user_id": user_id}

    def get_imap_config(self, user_id: str) -> dict:
        return {"status": "ok", "configured": True, "config": {"host": "imap.example.com"}, "user_id": user_id}

    def save_imap_config(self, user_id: str, payload: dict) -> dict:
        return {"status": "ok", "configured": True, "config": payload, "user_id": user_id}

    def test_imap_connection(self, user_id: str) -> dict:
        return {"status": "ok", "message": "IMAP connection successful", "user_id": user_id}

    def clear_imap_config(self, user_id: str) -> dict:
        return {"status": "ok", "message": "IMAP configuration removed", "user_id": user_id}


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-token"}
        return False, None


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_gmail_service] = lambda: _FakeGmailService()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
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


def test_gmail_oauth_callback_redirects():
    client = _client()

    response = client.get("/api/gmail/oauth/callback?code=abc", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://front/settings"


def test_gmail_messages_uses_token_when_user_id_missing():
    client = _client()

    response = client.get("/api/gmail/messages?max_results=12&force=true", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-token"


def test_gmail_messages_returns_400_without_user_or_token():
    client = _client()

    response = client.get("/api/gmail/messages")

    assert response.status_code == 400


def test_gmail_classify_unclassified_resolves_user_from_token():
    client = _client()

    response = client.get("/api/gmail/classify-unclassified?limit=50", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-token"


def test_gmail_message_body_uses_token_user():
    client = _client()

    response = client.get("/api/gmail/message/m-1", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["message_id"] == "m-1"
    assert response.json()["user_id"] == "u-token"


def test_imap_status_requires_auth():
    client = _client()

    response = client.get("/api/imap/status")

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_imap_status_uses_token_user():
    client = _client()

    response = client.get("/api/imap/status", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-token"


def test_imap_config_post_uses_payload_and_token():
    client = _client()

    response = client.post(
        "/api/imap/config",
        headers={"Authorization": "Bearer valid"},
        json={"host": "imap.example.com", "port": 993, "username": "user"},
    )

    assert response.status_code == 200
    assert response.json()["config"]["host"] == "imap.example.com"


def test_imap_test_and_clear_routes():
    client = _client()

    test_response = client.post("/api/imap/test", headers={"Authorization": "Bearer valid"})
    clear_response = client.delete("/api/imap/config", headers={"Authorization": "Bearer valid"})

    assert test_response.status_code == 200
    assert clear_response.status_code == 200
