from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository
from src.api.main import create_app


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

    def set_user_role(self, user_id: str, role: str):
        if user_id == "missing":
            return None
        return {
            "id": user_id,
            "email": f"{user_id}@example.com",
            "full_name": "Name",
            "role": role,
            "created_at": datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc),
        }


def test_admin_update_role_forbidden_for_non_admin():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-user")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNonAdmin()
    client = TestClient(app)

    response = client.patch(
        "/api/admin/users/u-target/role",
        headers={"Authorization": "Bearer valid"},
        json={"role": "admin"},
    )

    assert response.status_code == 403



def test_admin_update_role_rejects_invalid_role():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.patch(
        "/api/admin/users/u-target/role",
        headers={"Authorization": "Bearer valid"},
        json={"role": "superadmin"},
    )

    assert response.status_code == 400



def test_admin_update_role_prevents_self_demotion():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.patch(
        "/api/admin/users/u-admin/role",
        headers={"Authorization": "Bearer valid"},
        json={"role": "user"},
    )

    assert response.status_code == 400



def test_admin_update_role_returns_404_when_target_missing():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.patch(
        "/api/admin/users/missing/role",
        headers={"Authorization": "Bearer valid"},
        json={"role": "user"},
    )

    assert response.status_code == 404



def test_admin_update_role_success():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.patch(
        "/api/admin/users/u-target/role",
        headers={"Authorization": "Bearer valid"},
        json={"role": "admin"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["user"]["id"] == "u-target"
    assert payload["user"]["role"] == "admin"
    assert payload["user"]["created_at"].startswith("2026-01-03T10:00:00")
