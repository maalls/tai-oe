import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service
from src.api.main import create_app


class _FakeAuthService:
    def signup(self, email: str, password: str) -> dict:
        _ = (email, password)
        return {
            "status": 201,
            "user": {"id": "u_1", "email": "user@example.com"},
            "session": None,
        }


def test_auth_signup_returns_created_payload():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    client = TestClient(app)

    response = client.post("/api/auth/signup", json={"email": "user@example.com", "password": "secret"})

    assert response.status_code == 201
    assert response.json()["user"]["email"] == "user@example.com"


def test_auth_signup_rejects_invalid_email():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    client = TestClient(app)

    response = client.post("/api/auth/signup", json={"email": "invalid", "password": "secret"})

    assert response.status_code == 422
