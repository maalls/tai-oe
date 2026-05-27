import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-session"}
        return False, None


class _FakeDb:
    def __init__(self):
        self._profiles = {
            "u-session": {
                "id": "u-session",
                "email": "session@example.com",
                "full_name": "Session User",
                "role": "admin",
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        }

    def fetch_profile(self, user_id: str):
        return self._profiles.get(user_id)

    def list_users(self, limit: int = 100, offset: int = 0):
        _ = (limit, offset)
        return list(self._profiles.values())

    def delete_profile(self, user_id: str):
        self._profiles.pop(user_id, None)

    def set_role(self, user_id: str, role: str):
        if user_id in self._profiles:
            self._profiles[user_id]["role"] = role


def _build_client(db: _FakeDb) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: db
    return TestClient(app)


def test_admin_route_returns_401_for_invalid_token():
    db = _FakeDb()
    client = _build_client(db)

    response = client.get("/api/admin/users", headers={"Authorization": "Bearer expired"})

    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized"}


def test_admin_route_returns_403_for_non_admin_role():
    db = _FakeDb()
    db.set_role("u-session", "user")
    client = _build_client(db)

    response = client.get("/api/admin/users", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 403
    assert response.json() == {"error": "Forbidden"}


def test_admin_route_returns_explicit_error_when_profile_is_deleted():
    db = _FakeDb()
    db.delete_profile("u-session")
    client = _build_client(db)

    response = client.get("/api/admin/users", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 403
    assert response.json() == {"error": "Forbidden"}
