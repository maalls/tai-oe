import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_action_service, get_auth_service
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeActionService:
    def execute_action(self, action_id: str, user_id: str):
        return {"status": "ok", "action_id": action_id, "user_id": user_id}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_action_service] = lambda: _FakeActionService()
    return TestClient(app)


def test_execute_action_requires_auth():
    client = _client()

    response = client.post("/api/action/action-1/execute")

    assert response.status_code == 401


def test_execute_action_frontend_route_returns_payload():
    client = _client()

    response = client.post(
        "/api/action/action-1/execute",
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["action_id"] == "action-1"
    assert response.json()["user_id"] == "user-1"


def test_execute_action_legacy_alias_returns_payload():
    client = _client()

    response = client.post(
        "/api/actions/action-2/execute",
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["action_id"] == "action-2"