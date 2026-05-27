import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service
from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _AuthService:
    def __init__(self, valid=True):
        self.valid = valid

    def verify_token(self, token: str):
        if self.valid:
            return True, {"id": "user-1"}
        return False, None


class _DbFound:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}

    def execute_dict_query(self, query, params=None):
        assert params == (None, "doc-1")
        return [{"id": "doc-1", "opportunity_id": "opp-1", "storage_key": None}]


class _DbMissing:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}

    def execute_dict_query(self, query, params=None):
        return []


class _DbNonAdmin(_DbFound):
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "user"}


def test_document_update_storage_key_requires_auth():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=False)
    app.dependency_overrides[get_database_repository] = lambda: _DbFound()
    client = TestClient(app)

    response = client.put("/api/document/doc-1/storage-key", json={"storage_key": None})

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_document_update_storage_key_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=True)
    app.dependency_overrides[get_database_repository] = lambda: _DbMissing()
    client = TestClient(app)

    response = client.put(
        "/api/document/doc-1/storage-key",
        json={"storage_key": None},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Document not found"


def test_document_update_storage_key_returns_row():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=True)
    app.dependency_overrides[get_database_repository] = lambda: _DbFound()
    client = TestClient(app)

    response = client.put(
        "/api/document/doc-1/storage-key",
        json={"storage_key": None},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "doc-1"
    assert response.json()["storage_key"] is None


def test_document_update_storage_key_forbidden_for_non_admin():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=True)
    app.dependency_overrides[get_database_repository] = lambda: _DbNonAdmin()
    client = TestClient(app)

    response = client.put(
        "/api/document/doc-1/storage-key",
        json={"storage_key": None},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"