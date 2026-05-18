import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service
from src.api.document.router import get_db
from src.api.main import create_app


class _AuthService:
    def __init__(self, valid=True):
        self.valid = valid

    def verify_token(self, token: str):
        if self.valid:
            return True, {"id": "user-1"}
        return False, None


class _DbFound:
    def execute_dict_query(self, query, params=None):
        assert params == ("PAID", "doc-1")
        return [{"id": "doc-1", "opportunity_id": "opp-1", "status": "PAID"}]


class _DbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_document_update_status_requires_auth():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=False)
    app.dependency_overrides[get_db] = lambda: _DbFound()
    client = TestClient(app)

    response = client.put("/api/document/doc-1/status", json={"status": "PAID"})

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_document_update_status_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=True)
    app.dependency_overrides[get_db] = lambda: _DbMissing()
    client = TestClient(app)

    response = client.put(
        "/api/document/doc-1/status",
        json={"status": "PAID"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Document not found"


def test_document_update_status_returns_row():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthService(valid=True)
    app.dependency_overrides[get_db] = lambda: _DbFound()
    client = TestClient(app)

    response = client.put(
        "/api/document/doc-1/status",
        json={"status": "PAID"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "doc-1"
    assert response.json()["status"] == "PAID"