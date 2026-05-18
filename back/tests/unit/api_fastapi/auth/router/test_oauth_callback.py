import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_oauth_service
from src.api_fastapi.main import create_app


class _FakeOAuthService:
    def exchange_callback(self, provider: str, code: str, state: str | None = None) -> dict:
        _ = (provider, code, state)
        return {
            "status": "ok",
            "redirect_url": "https://example.com/done",
        }


def test_oauth_callback_redirects_when_result_contains_redirect_url():
    app = create_app()
    app.dependency_overrides[get_oauth_service] = lambda: _FakeOAuthService()
    client = TestClient(app)

    response = client.get("/api/oauth/callback?provider=google&code=abc", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/done"
