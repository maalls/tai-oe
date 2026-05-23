import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_outlook_service
from src.api.main import create_app


class _FakeOutlookService:
    def get_status(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "authorized": True, "user_id": user_id}

    def get_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict:
        return {
            "status": "ok",
            "auth_url": "https://example.com/outlook/start",
            "redirect_url": redirect_url,
            "user_id": user_id,
        }

    def oauth_callback(self, code: str, state: str | None = None) -> dict:
        _ = (code, state)
        return {"status": "ok", "redirect_url": "https://front/settings"}

    def revoke(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "message": "revoked", "user_id": user_id}

    def get_profile(self, user_id: str | None = None) -> dict:
        return {"status": "ok", "profile": {"mail": "user@example.com"}, "user_id": user_id}

    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False) -> dict:
        return {"status": "ok", "messages": [], "user_id": user_id, "max_results": max_results, "force": force}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_outlook_service] = lambda: _FakeOutlookService()
    return TestClient(app)


def test_outlook_status_route_uses_query_user_id():
    client = _client()

    response = client.get("/api/outlook/status?user_id=u-1")

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-1"


def test_outlook_status_not_authorized_returns_200_with_payload():
    class _NotAuthorizedOutlookService(_FakeOutlookService):
        def get_status(self, user_id: str | None = None) -> dict:
            return {
                "status": "error",
                "authorized": False,
                "error_code": "OUTLOOK_NOT_AUTHORIZED",
                "message": "Outlook not authorized. Please authorize first.",
                "user_id": user_id,
            }

    app = create_app()
    app.dependency_overrides[get_outlook_service] = lambda: _NotAuthorizedOutlookService()
    client = TestClient(app)

    response = client.get("/api/outlook/status?user_id=u-1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["error_code"] == "OUTLOOK_NOT_AUTHORIZED"


def test_outlook_oauth_start_route_supports_user_context():
    client = _client()

    response = client.get("/api/outlook/oauth/start?redirect_url=https://front/settings&user_id=u-2")

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-2"


def test_outlook_oauth_callback_redirects():
    client = _client()

    response = client.get("/api/outlook/oauth/callback?code=abc", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://front/settings"


def test_outlook_revoke_accepts_post_method():
    client = _client()

    response = client.post("/api/outlook/revoke?user_id=u-3")

    assert response.status_code == 200
    assert response.json()["message"] == "revoked"
