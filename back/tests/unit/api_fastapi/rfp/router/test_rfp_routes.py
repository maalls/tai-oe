import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_service_factory
from src.api_fastapi.main import create_app
from src.domain.enums import DocumentStatus
from src.domain.rfp import Rfp


class _FakeRfpService:
    def get_rfp(self, rfp_id: str):
        if rfp_id == "missing":
            raise ValueError("RFP not found")
        return Rfp(
            id=rfp_id,
            title="RFP",
            requester_email="test@example.com",
            content="hello",
            status=DocumentStatus.DRAFT,
        )

    def submit_rfp(self, rfp_id: str):
        if rfp_id == "missing":
            raise ValueError("RFP not found")
        return Rfp(
            id=rfp_id,
            title="RFP",
            requester_email="test@example.com",
            content="hello",
            status=DocumentStatus.SUBMITTED,
        )


class _FakeServiceFactory:
    def create_rfp_service(self):
        return _FakeRfpService()


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_service_factory] = lambda: _FakeServiceFactory()
    return TestClient(app)


def test_get_rfp_requires_query_param():
    client = _client()

    response = client.get("/api/ddd/rfp")

    assert response.status_code == 400
    assert response.json()["message"] == "Missing rfp_id"


def test_get_rfp_returns_payload():
    client = _client()

    response = client.get("/api/ddd/rfp?rfp_id=rfp-1")

    assert response.status_code == 200
    assert response.json()["rfp"]["id"] == "rfp-1"
    assert response.json()["rfp"]["status"] == "DRAFT"


def test_submit_rfp_get_returns_payload():
    client = _client()

    response = client.get("/api/ddd/rfp/submit?rfp_id=rfp-1")

    assert response.status_code == 200
    assert response.json()["rfp"]["status"] == "SUBMITTED"


def test_submit_rfp_post_returns_payload():
    client = _client()

    response = client.post("/api/ddd/rfp/submit", json={"rfp_id": "rfp-1"})

    assert response.status_code == 200
    assert response.json()["rfp"]["status"] == "SUBMITTED"


def test_get_rfp_returns_error_when_service_fails():
    client = _client()

    response = client.get("/api/ddd/rfp?rfp_id=missing")

    assert response.status_code == 400
    assert response.json()["status"] == "error"
