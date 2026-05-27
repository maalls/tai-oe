import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository, get_service_factory
from src.api.main import create_app
from src.domain.enums import OpportunityStage, OpportunityStatus
from src.domain.opportunity import Opportunity


class _FakeOpportunityService:
    def get_opportunity(self, opportunity_id: str):
        if opportunity_id == "missing":
            raise ValueError("Opportunity not found")
        return Opportunity(
            id=opportunity_id,
            owner_user_id=None,
            account_id="acc-1",
            name="Deal",
            stage=OpportunityStage.NEW_LEAD,
            status=OpportunityStatus.OPEN,
        )

    def advance_opportunity(self, opportunity_id: str, stage: OpportunityStage):
        if opportunity_id == "missing":
            raise ValueError("Opportunity not found")
        return Opportunity(
            id=opportunity_id,
            owner_user_id=None,
            account_id="acc-1",
            name="Deal",
            stage=stage,
            status=OpportunityStatus.OPEN,
        )


class _FakeServiceFactory:
    def create_opportunity_service(self):
        return _FakeOpportunityService()


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeDb:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_service_factory] = lambda: _FakeServiceFactory()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    return TestClient(app)


def test_get_opportunity_requires_query_param():
    client = _client()

    response = client.get("/api/opportunity", headers={"Authorization": "Bearer ok"})

    assert response.status_code == 400
    assert response.json()["message"] == "Missing opportunity_id"


def test_get_opportunity_returns_payload():
    client = _client()

    response = client.get("/api/opportunity?opportunity_id=opp-1", headers={"Authorization": "Bearer ok"})

    assert response.status_code == 200
    assert response.json()["opportunity"]["id"] == "opp-1"
    assert response.json()["opportunity"]["stage"] == "NEW_LEAD"


def test_advance_opportunity_get_requires_stage():
    client = _client()

    response = client.get("/api/opportunity/advance?opportunity_id=opp-1", headers={"Authorization": "Bearer ok"})

    assert response.status_code == 400
    assert response.json()["message"] == "Missing stage"


def test_advance_opportunity_get_returns_payload():
    client = _client()

    response = client.get(
        "/api/opportunity/advance?opportunity_id=opp-1&stage=NEGOTIATION",
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity"]["stage"] == "NEGOTIATION"


def test_advance_opportunity_post_returns_payload():
    client = _client()

    response = client.post(
        "/api/opportunity/advance",
        json={"opportunity_id": "opp-1", "stage": "COMMITMENT"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["opportunity"]["stage"] == "COMMITMENT"


def test_get_opportunity_returns_error_when_service_fails():
    client = _client()

    response = client.get("/api/opportunity?opportunity_id=missing", headers={"Authorization": "Bearer ok"})

    assert response.status_code == 400
    assert response.json()["status"] == "error"
