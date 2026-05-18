from fastapi.testclient import TestClient

import src.api.profile.router as profile_router
from src.api.dependencies import get_auth_service
from src.api.main import create_app


class _FakeDbOk:
    def fetch_profile(self, user_id):
        assert user_id == "user-1"
        return {"id": "user-1", "email": "user@example.com", "full_name": "Jane"}


class _FakeDbMissing:
    def fetch_profile(self, user_id):
        return None


def test_get_profile_returns_profile(monkeypatch):
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: "user-1"
    monkeypatch.setattr(profile_router, "DatabaseRepository", lambda: _FakeDbOk())
    client = TestClient(app)

    response = client.get("/api/profile")

    assert response.status_code == 200
    assert response.json()["id"] == "user-1"


def test_get_profile_returns_404_when_missing(monkeypatch):
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: "user-1"
    monkeypatch.setattr(profile_router, "DatabaseRepository", lambda: _FakeDbMissing())
    client = TestClient(app)

    response = client.get("/api/profile")

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"
