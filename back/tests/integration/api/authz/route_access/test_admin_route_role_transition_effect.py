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


class _MutableFakeDb:
    def __init__(self):
        self._profiles = {
            "u-session": {
                "id": "u-session",
                "email": "session@example.com",
                "full_name": "Session User",
                "role": "admin",
                "created_at": "2026-01-01T00:00:00+00:00",
            },
            "u-target": {
                "id": "u-target",
                "email": "target@example.com",
                "full_name": "Target User",
                "role": "user",
                "created_at": "2026-01-02T00:00:00+00:00",
            },
        }

    def fetch_profile(self, user_id: str):
        return self._profiles.get(user_id)

    def list_users(self, limit: int = 100, offset: int = 0):
        _ = (limit, offset)
        return list(self._profiles.values())

    def force_role(self, user_id: str, role: str):
        if user_id in self._profiles:
            self._profiles[user_id]["role"] = role


def _build_client(db: _MutableFakeDb) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: db
    return TestClient(app)


def test_admin_route_access_changes_immediately_after_role_demote_then_promote():
    db = _MutableFakeDb()
    client = _build_client(db)
    headers = {"Authorization": "Bearer valid"}

    before_change = client.get("/api/admin/users", headers=headers)
    assert before_change.status_code == 200

    db.force_role("u-session", "user")
    after_demote = client.get("/api/admin/users", headers=headers)
    assert after_demote.status_code == 403
    assert after_demote.json() == {"error": "Forbidden"}

    db.force_role("u-session", "admin")
    after_promote = client.get("/api/admin/users", headers=headers)
    assert after_promote.status_code == 200


def test_admin_route_access_changes_immediately_after_role_promote():
    db = _MutableFakeDb()
    db.force_role("u-session", "user")
    client = _build_client(db)
    headers = {"Authorization": "Bearer valid"}

    before_promote = client.get("/api/admin/users", headers=headers)
    assert before_promote.status_code == 403

    db.force_role("u-session", "admin")
    after_promote = client.get("/api/admin/users", headers=headers)
    assert after_promote.status_code == 200
