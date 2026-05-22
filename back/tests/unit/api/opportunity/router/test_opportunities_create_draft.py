import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

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
    def execute_dict_query(self, query, params=None):
        if "INSERT INTO opportunity" in query:
            return [
                {
                    "id": "opp-9",
                    "account_id": params[1],
                    "name": params[2],
                    "stage": "NEW_LEAD",
                    "status": "OPEN",
                    "source": params[3],
                }
            ]
        return []


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    return TestClient(app)


def test_opportunities_create_draft_requires_auth():
    client = _client()

    response = client.post("/api/opportunities/create-draft", json={"account_id": "a-1"})

    assert response.status_code == 401


def test_opportunities_create_draft_returns_payload():
    client = _client()

    response = client.post(
        "/api/opportunities/create-draft",
        json={"account_id": "a-1", "name": "", "source": "user_form"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity"]["id"] == "opp-9"
    assert response.json()["opportunity"]["account_id"] == "a-1"