import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_gmail_service
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer ok":
            return True, {"id": "u-int"}
        return False, None


class _FakeGmailService:
    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False):
        return {
            "status": "ok",
            "messages": [],
            "user_id": user_id,
            "max_results": max_results,
            "force": force,
        }


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_gmail_service] = lambda: _FakeGmailService()
    return TestClient(app)


def test_healthz_returns_ok():
    client = _client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_gmail_messages_requires_user_or_valid_token():
    client = _client()

    response = client.get("/api/gmail/messages")

    assert response.status_code == 400
    assert response.json()["message"] == "Missing user_id"


def test_gmail_messages_accepts_valid_token():
    client = _client()

    response = client.get("/api/gmail/messages?max_results=5&force=true", headers={"Authorization": "Bearer ok"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "u-int"
    assert payload["max_results"] == 5
    assert payload["force"] is True
