import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository, get_opportunity_repository
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeOpportunityHandlers:
    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        return {"status": "ok", "opportunity_id": opportunity_id, "user_id": user_id}


class _FakeDatabaseRepository:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_opportunity_repository] = lambda: _FakeOpportunityHandlers()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepository()
    return TestClient(app)


def test_opportunity_rfq_generate_requires_auth():
    client = _client()

    response = client.post("/api/opportunity/opp-1/rfq/generate")

    assert response.status_code == 401


def test_opportunity_rfq_generate_returns_payload():
    client = _client()

    response = client.post(
        "/api/opportunity/opp-1/rfq/generate",
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity_id"] == "opp-1"
