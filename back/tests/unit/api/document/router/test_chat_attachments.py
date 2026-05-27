import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository, get_document_service
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-1"}
        return False, None


class _FakeDocumentService:
    def handle_chat_attachment_upload(
        self,
        filename: str,
        file_content: bytes,
        mime_type: str,
        file_size: int,
        user_id: str,
        opportunity_id: str,
    ):
        return {
            "status": "ok",
            "document_id": "doc-attach-1",
            "filename": filename,
            "size": file_size,
            "mime_type": mime_type,
            "user_id": user_id,
            "opportunity_id": opportunity_id,
            "content": file_content.decode("utf-8"),
        }


class _FakeDbAdmin:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


class _FakeDbNonAdmin(_FakeDbAdmin):
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "user"}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbAdmin()
    app.dependency_overrides[get_document_service] = lambda: _FakeDocumentService()
    return TestClient(app)


def test_chat_attachments_requires_auth():
    client = _client()

    response = client.post(
        "/api/chat/attachments?opportunity_id=opp-1",
        files={"file": ("hello.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 401


def test_chat_attachments_returns_payload():
    client = _client()

    response = client.post(
        "/api/chat/attachments?opportunity_id=opp-1",
        headers={"Authorization": "Bearer valid"},
        files={"file": ("hello.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "hello.txt"
    assert response.json()["opportunity_id"] == "opp-1"
    assert response.json()["content"] == "hello"


def test_chat_attachments_forbidden_for_non_admin():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNonAdmin()
    app.dependency_overrides[get_document_service] = lambda: _FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        "/api/chat/attachments?opportunity_id=opp-1",
        headers={"Authorization": "Bearer valid"},
        files={"file": ("hello.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"
