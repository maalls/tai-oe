import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_document_service
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-1"}
        return False, None


class _FakeDocumentService:
    def handle_update_document_content(self, document_id: str, content: str, user_id: str | None = None):
        return {"status": "ok", "document_id": document_id, "content": content, "user_id": user_id}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_document_service] = lambda: _FakeDocumentService()
    return TestClient(app)


def test_document_update_content_requires_auth():
    client = _client()

    response = client.post("/api/document/update-content", json={"document_id": "doc-1", "content": "hello"})

    assert response.status_code == 401


def test_document_update_content_returns_payload():
    client = _client()

    response = client.post(
        "/api/document/update-content",
        headers={"Authorization": "Bearer valid"},
        json={"document_id": "doc-1", "content": "hello"},
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-1"
    assert response.json()["content"] == "hello"
