import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_auth_service, get_rfq_handlers
from src.api_fastapi.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-1"}
        return False, None


class _FakeRfqHandlers:
    def handle_rfq_generate(self, text: str | None = None, message_id: str | None = None, user_id: str | None = None):
        if not text and not message_id:
            return {"status": "error", "message": "No text provided and unable to load email body"}
        return {"status": "ok", "rfq_id": "rfq-1", "user_id": user_id}

    def handle_rfp_upload(self, body: bytes, content_type: str):
        if "multipart/form-data" not in content_type:
            return {"status": "error", "message": "Invalid content type"}
        return {"status": "ok", "message": "RFP received successfully", "size": len(body)}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_rfq_handlers] = lambda: _FakeRfqHandlers()
    return TestClient(app)


def test_rfq_generate_requires_auth():
    client = _client()

    response = client.post("/api/rfq/generate", json={"text": "hello"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


def test_rfq_generate_returns_payload():
    client = _client()

    response = client.post("/api/rfq/generate", headers={"Authorization": "Bearer valid"}, json={"text": "hello"})

    assert response.status_code == 200
    assert response.json()["rfq_id"] == "rfq-1"


def test_rfp_upload_returns_payload():
    client = _client()

    response = client.post(
        "/api/rfp",
        files={"file": ("sample.txt", b"data", "text/plain")},
        data={"message": "hello"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
