import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository
from src.api.main import create_app


class _FakeAuthService:
    def get_user(self, auth_header: str) -> dict:
        _ = auth_header
        return {
            "status": 200,
            "user": {
                "id": "user-1",
                "email": "user@example.com",
            },
        }


class _FakeDbWithRole:
    def fetch_profile(self, user_id: str):
        assert user_id == "user-1"
        return {"id": "user-1", "role": "admin"}


class _FakeDbMissingRole:
    def fetch_profile(self, user_id: str):
        assert user_id == "user-1"
        return None


def test_auth_user_returns_role_from_profile():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbWithRole()
    client = TestClient(app)

    response = client.get("/api/auth/user", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_auth_user_defaults_role_to_user_when_profile_missing():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbMissingRole()
    client = TestClient(app)

    response = client.get("/api/auth/user", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"
