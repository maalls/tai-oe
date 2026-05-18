import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_opportunity_repository
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeOpportunityHandlers:
    def search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None):
        return {
            "status": "ok",
            "opportunities": [{"id": "opp-1", "owner_user_id": user_id}],
            "source_reference_id": source_reference_id,
            "name": name,
        }


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_opportunity_repository] = lambda: _FakeOpportunityHandlers()
    return TestClient(app)


def test_opportunities_search_requires_auth():
    client = _client()

    response = client.get("/api/opportunities/search")

    assert response.status_code == 401


def test_opportunities_search_returns_payload():
    client = _client()

    response = client.get(
        "/api/opportunities/search?name=deal",
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunities"][0]["id"] == "opp-1"
    assert response.json()["name"] == "deal"
