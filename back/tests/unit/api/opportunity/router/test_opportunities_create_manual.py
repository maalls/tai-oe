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
    def create_opportunity_manual(self, user_id: str, name: str):
        return {"status": "ok", "opportunity": {"id": "opp-2", "name": name, "owner_user_id": user_id}}


class _FakeDatabaseRepository:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_opportunity_repository] = lambda: _FakeOpportunityHandlers()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepository()
    return TestClient(app)


def test_opportunities_create_manual_requires_auth():
    client = _client()

    response = client.post("/api/opportunities/create-manual", json={"name": "Deal"})

    assert response.status_code == 401


def test_opportunities_create_manual_returns_payload():
    client = _client()

    response = client.post(
        "/api/opportunities/create-manual",
        json={"name": "Deal"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity"]["name"] == "Deal"
