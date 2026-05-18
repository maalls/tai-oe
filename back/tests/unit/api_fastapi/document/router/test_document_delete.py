import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_auth_service, get_document_service
from src.api_fastapi.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-1"}
        return False, None


class _FakeDocumentService:
    def handle_delete_document(self, document_id: str, user_id: str | None = None):
        return {"status": "ok", "document_id": document_id, "user_id": user_id}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_document_service] = lambda: _FakeDocumentService()
    return TestClient(app)


def test_document_delete_requires_auth():
    client = _client()

    response = client.delete("/api/document/doc-1")

    assert response.status_code == 401


def test_document_delete_returns_payload():
    client = _client()

    response = client.delete(
        "/api/document/doc-1",
        headers={"Authorization": "Bearer valid"},
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-1"
