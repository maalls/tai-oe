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

    def signup(self, email: str, password: str):
        _ = password
        if email == "exists@example.com":
            return {"status": 400, "error": "User already registered"}

        return {
            "status": 201,
            "user": {"id": "u-created", "email": email},
            "session": None,
        }


class _FakeDbNonAdmin:
    def fetch_profile(self, user_id: str):
        _ = user_id
        return {"id": "u-1", "role": "user"}


class _FakeDbAdmin:
    def __init__(self):
        self.updated_role = None
        self.updated_profile = None

    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}

    def set_user_role(self, user_id: str, role: str):
        self.updated_role = (user_id, role)
        return {
            "id": user_id,
            "email": "created@example.com",
            "full_name": None,
            "role": role,
            "created_at": datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc),
        }

    def update_profile(self, user_id: str, updates: dict):
        self.updated_profile = (user_id, updates)
        return {
            "id": user_id,
            "email": "created@example.com",
            "full_name": updates.get("full_name"),
            "role": "user",
        }

    def get_user_by_id(self, user_id: str):
        role = "user"
        if self.updated_role and self.updated_role[0] == user_id:
            role = self.updated_role[1]

        full_name = None
        if self.updated_profile and self.updated_profile[0] == user_id:
            full_name = self.updated_profile[1].get("full_name")

        return {
            "id": user_id,
            "email": "created@example.com",
            "full_name": full_name,
            "role": role,
            "created_at": datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc),
        }


def test_admin_create_user_forbidden_for_non_admin():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-user")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNonAdmin()
    client = TestClient(app)

    response = client.post(
        "/api/admin/users",
        headers={"Authorization": "Bearer valid"},
        json={"email": "new@example.com", "password": "secret-123"},
    )

    assert response.status_code == 403


def test_admin_create_user_requires_valid_token():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceInvalid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNonAdmin()
    client = TestClient(app)

    response = client.post(
        "/api/admin/users",
        json={"email": "new@example.com", "password": "secret-123"},
    )

    assert response.status_code == 401


def test_admin_create_user_rejects_invalid_payload():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.post(
        "/api/admin/users",
        headers={"Authorization": "Bearer valid"},
        json={"email": "invalid", "password": "secret-123", "role": "owner"},
    )

    assert response.status_code == 400


def test_admin_create_user_propagates_signup_errors():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    client = TestClient(app)

    response = client.post(
        "/api/admin/users",
        headers={"Authorization": "Bearer valid"},
        json={"email": "exists@example.com", "password": "secret-123", "role": "user"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "User already registered"


def test_admin_create_user_success_with_role_and_name():
    app = create_app()
    fake_db = _FakeDbAdmin()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid("u-admin")
    app.dependency_overrides[get_database_repository] = lambda: fake_db
    client = TestClient(app)

    response = client.post(
        "/api/admin/users",
        headers={"Authorization": "Bearer valid"},
        json={
            "email": "created@example.com",
            "password": "secret-123",
            "full_name": "Created User",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["user"]["id"] == "u-created"
    assert payload["user"]["role"] == "admin"
    assert payload["user"]["full_name"] == "Created User"
