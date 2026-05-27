from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service
from src.api.main import create_app
from src.api.dependencies import get_database_repository


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeDb:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}

    def execute_dict_query(self, query, params=None):
        if "UPDATE opportunity" in query:
            if params[1] == "missing":
                return []
            return [{"id": params[1], "account_id": params[0], "name": "Deal"}]
        return []


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    return TestClient(app)


def test_opportunity_update_account_requires_auth():
    client = _client()

    response = client.put("/api/opportunity/opp-1/account", json={"account_id": "a-1"})

    assert response.status_code == 401


def test_opportunity_update_account_returns_row():
    client = _client()

    response = client.put(
        "/api/opportunity/opp-1/account",
        json={"account_id": "a-1"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "opp-1"
    assert response.json()["account_id"] == "a-1"


def test_opportunity_update_account_returns_404_when_missing():
    client = _client()

    response = client.put(
        "/api/opportunity/missing/account",
        json={"account_id": "a-1"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found"