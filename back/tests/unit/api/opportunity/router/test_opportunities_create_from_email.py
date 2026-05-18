import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_email_repository, get_opportunity_repository
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeEmailHandlers:
    def create_opportunity_from_email(self, message_id: str, user_id: str = None):
        return {"status": "ok", "opportunity": {"id": "opp-3"}, "message_id": message_id, "user_id": user_id}


class _FakeOpportunityHandlers:
    def __init__(self):
        self.generated = None

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        self.generated = (opportunity_id, user_id)
        return {"status": "ok"}


def _client(fake_opportunity_handlers: _FakeOpportunityHandlers) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_email_repository] = lambda: _FakeEmailHandlers()
    app.dependency_overrides[get_opportunity_repository] = lambda: fake_opportunity_handlers
    return TestClient(app)


def test_opportunities_create_from_email_requires_auth():
    fake_opp = _FakeOpportunityHandlers()
    client = _client(fake_opp)

    response = client.post("/api/opportunities/create-from-email", json={"message_id": "m-1"})

    assert response.status_code == 401


def test_opportunities_create_from_email_returns_payload_and_triggers_quote():
    fake_opp = _FakeOpportunityHandlers()
    client = _client(fake_opp)

    response = client.post(
        "/api/opportunities/create-from-email",
        json={"message_id": "m-1"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity"]["id"] == "opp-3"
    assert fake_opp.generated == ("opp-3", "user-1")
