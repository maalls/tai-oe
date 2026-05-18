import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_auth_service, get_rfq_source_service
from src.api_fastapi.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeRfqSourceService:
    def create_rfq_source_from_html_body(self, opportunity_id: str, body: bytes, content_type: str, user_id: str = None):
        return {
            "status": "ok",
            "kind": "new" if opportunity_id == "new" else "existing",
            "opportunity_id": opportunity_id,
            "opportunity": {"id": "opp-new"} if opportunity_id == "new" else {"id": opportunity_id},
            "content_type": content_type,
            "user_id": user_id,
            "size": len(body),
        }


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_rfq_source_service] = lambda: _FakeRfqSourceService()
    return TestClient(app)


def test_opportunity_rfq_create_from_text_requires_auth():
    client = _client()

    response = client.post("/api/opportunity/opp-1/rfq/create-from-text", data={"message": "hello"})

    assert response.status_code == 401


def test_opportunity_rfq_create_from_text_existing_opportunity():
    client = _client()

    response = client.post(
        "/api/opportunity/opp-1/rfq/create-from-text",
        data={"message": "hello"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "existing"
    assert response.json()["opportunity_id"] == "opp-1"


def test_opportunity_rfq_create_from_text_new_opportunity_triggers_quote_generation():
    client = _client()

    response = client.post(
        "/api/opportunity/new/rfq/create-from-text",
        data={"message": "hello"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "new"
    assert response.json()["opportunity"]["id"] == "opp-new"
