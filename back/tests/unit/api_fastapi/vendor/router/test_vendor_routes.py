import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_service_factory
from src.api_fastapi.main import create_app


class _FakeVendor:
    def __init__(self, vendor_id: str, name: str):
        self.id = vendor_id
        self.name = name
        self.email = None
        self.phone = None
        self.website = None
        self.created_at = None


class _FakeVendorService:
    def get_vendor(self, vendor_id: str):
        if vendor_id == "missing":
            raise ValueError("Vendor not found")
        return _FakeVendor(vendor_id, "ACME")


class _FakeServiceFactory:
    def create_vendor_service(self):
        return _FakeVendorService()


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_service_factory] = lambda: _FakeServiceFactory()
    return TestClient(app)


def test_vendor_requires_vendor_id_query_param():
    client = _client()

    response = client.get("/api/ddd/vendor")

    assert response.status_code == 400
    assert response.json()["message"] == "Missing vendor_id"


def test_vendor_returns_payload():
    client = _client()

    response = client.get("/api/ddd/vendor?vendor_id=v-1")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["vendor"]["id"] == "v-1"


def test_vendor_returns_error_when_service_fails():
    client = _client()

    response = client.get("/api/ddd/vendor?vendor_id=missing")

    assert response.status_code == 400
    assert response.json()["status"] == "error"
