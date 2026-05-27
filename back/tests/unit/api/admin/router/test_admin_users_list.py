from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository
from src.api.main import create_app


class _FakeAuthServiceInvalid:
    def verify_token(self, auth_header: str):
        _ = auth_header
        return False, None


class _FakeAuthServiceValid:
    def __init__(self, user_id: str):
        self._user_id = user_id

    def verify_token(self, auth_header: str):
        _ = auth_header
        return True, {"id": self._user_id}


class _FakeDbNonAdmin:
    def fetch_profile(self, user_id: str):
        _ = user_id
        return {"id": "u-1", "role": "user"}


class _FakeDbAdmin:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}

    def list_users(self, limit: int = 100, offset: int = 0):
        assert limit == 100
        assert offset == 0
        return [
            {
                "id": "u-1",
                "email": "admin@example.com",
                "full_name": "Admin",
                "role": "admin",
                "created_at": datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
            },
            {
                "id": "u-2",
                "email": "user@example.com",
                "full_name": "User",
                "role": "user",
                "created_at": datetime(2026, 1, 2, 8, 30, tzinfo=timezone.utc),
            },
        ]


def test_admin_users_list_requires_valid_token():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceInvalid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNonAdmin()
    client = TestClient(app)

    response = client.get("/api/admin/users")

    assert response.status_code == 401



def test_admin_users_list_forbidden_for_non_admin():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-user")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNonAdmin()
    client = TestClient(app)

    response = client.get("/api/admin/users", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 403



def test_admin_users_list_returns_users_for_admin():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.get("/api/admin/users", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert len(payload["users"]) == 2
    assert payload["users"][0]["role"] == "admin"
    assert payload["users"][0]["created_at"].startswith("2026-01-01T08:30:00")
