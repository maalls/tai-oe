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
    def delete_opportunities(self, opportunity_ids: list[str], user_id: str = None):
        return {"status": "ok", "deleted_count": len(opportunity_ids), "ids": opportunity_ids, "user_id": user_id}


class _FakeDatabaseRepository:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_opportunity_repository] = lambda: _FakeOpportunityHandlers()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepository()
    return TestClient(app)


def test_opportunities_delete_requires_auth():
    client = _client()

    response = client.delete("/api/opportunities/opp-1,opp-2")

    assert response.status_code == 401


def test_opportunities_delete_splits_csv_ids():
    client = _client()

    response = client.delete(
        "/api/opportunities/opp-1,opp-2",
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["ids"] == ["opp-1", "opp-2"]
    assert response.json()["deleted_count"] == 2
