import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository, get_quote_send_service
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeEmailHandlers:
    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: dict, user_id: str = None):
        return {
            "status": "ok",
            "opportunity_id": opportunity_id,
            "payload": payload,
            "user_id": user_id,
        }


class _FakeDatabaseRepository:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_quote_send_service] = lambda: _FakeEmailHandlers()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepository()
    return TestClient(app)


def test_opportunity_send_quote_requires_auth():
    client = _client()

    response = client.post("/api/opportunity/opp-1/send-quote", json={"to": ["a@b.com"]})

    assert response.status_code == 401


def test_opportunity_send_quote_returns_payload():
    client = _client()

    response = client.post(
        "/api/opportunity/opp-1/send-quote",
        json={"to": ["a@b.com"]},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity_id"] == "opp-1"
    assert response.json()["payload"]["to"] == ["a@b.com"]
