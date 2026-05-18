import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_gmail_service
from src.api.main import create_app


class _FakeGmailService:
    def list_attachments(self, email_id: str, user_id: str) -> dict:
        return {
            "status": "ok",
            "attachments": [
                {
                    "id": "att-1",
                    "filename": "quote.pdf",
                    "mime_type": "application/pdf",
                    "size": 123,
                    "storage_path": "/tmp/quote.pdf",
                }
            ],
            "email_id": email_id,
            "user_id": user_id,
        }


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-token"}
        return False, None


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_gmail_service] = lambda: _FakeGmailService()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    return TestClient(app)


def test_email_attachments_list_requires_auth():
    client = _client()

    response = client.get('/api/email/e-1/attachments')

    assert response.status_code == 401
    assert response.json() == {'error': 'Unauthorized'}


def test_email_attachments_list_returns_payload():
    client = _client()

    response = client.get('/api/email/e-1/attachments', headers={'Authorization': 'Bearer valid'})

    assert response.status_code == 200
    assert response.json()['attachments'][0]['id'] == 'att-1'
    assert response.json()['email_id'] == 'e-1'
    assert response.json()['user_id'] == 'u-token'