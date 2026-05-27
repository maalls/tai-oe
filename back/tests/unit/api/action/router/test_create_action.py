import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_action_service, get_auth_service, get_database_repository
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeDatabaseRepositoryAdmin:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


class _FakeDatabaseRepositoryUser:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "user"}


class _FakeActionService:
    def create_action(self, payload: dict, user_id: str | None = None):
        return {"id": "a-1", "payload": payload, "user_id": user_id}


def _client(*, non_admin: bool = False) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_action_service] = lambda: _FakeActionService()
    app.dependency_overrides[get_database_repository] = (
        (lambda: _FakeDatabaseRepositoryUser())
        if non_admin
        else (lambda: _FakeDatabaseRepositoryAdmin())
    )
    return TestClient(app)


def test_create_action_requires_auth():
    client = _client()

    response = client.post("/api/actions", json={"type": "task"})

    assert response.status_code == 401


def test_create_action_returns_forbidden_for_non_admin_role():
    client = _client(non_admin=True)

    response = client.post(
        "/api/actions",
        headers={"Authorization": "Bearer ok"},
        json={"type": "task"},
    )

    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"


def test_create_action_returns_payload_for_admin():
    client = _client()

    response = client.post(
        "/api/actions",
        headers={"Authorization": "Bearer ok"},
        json={"type": "task"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["action"]["user_id"] == "user-1"
