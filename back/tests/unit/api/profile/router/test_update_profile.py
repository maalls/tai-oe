from fastapi.testclient import TestClient

import src.api.profile.router as profile_router
from src.api.dependencies import get_auth_service
from src.api.main import create_app


class _FakeDbOk:
    def update_profile(self, user_id, updates):
        assert user_id == "user-1"
        assert updates == {"full_name": "Jane Updated"}
        return {"id": "user-1", "email": "user@example.com", "full_name": "Jane Updated"}


class _FakeDbMissing:
    def update_profile(self, user_id, updates):
        return None


def test_update_profile_returns_updated_profile(monkeypatch):
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: "user-1"
    monkeypatch.setattr(profile_router, "DatabaseRepository", lambda: _FakeDbOk())
    client = TestClient(app)

    response = client.put("/api/profile", json={"full_name": "Jane Updated"})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane Updated"


def test_update_profile_returns_404_when_missing(monkeypatch):
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: "user-1"
    monkeypatch.setattr(profile_router, "DatabaseRepository", lambda: _FakeDbMissing())
    client = TestClient(app)

    response = client.put("/api/profile", json={"full_name": "Jane Updated"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"
