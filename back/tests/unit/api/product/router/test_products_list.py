import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_product_service
from src.api.main import create_app


class _FakeProductService:
    def list_products(self, qs: dict):
        return [{"id": "p-1", "qs": qs}]


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_product_service] = lambda: _FakeProductService()
    return TestClient(app)


def test_products_list_returns_payload():
    client = _client()

    response = client.get("/api/products?sku=ABC&limit=5")

    assert response.status_code == 200
    assert response.json()["products"][0]["id"] == "p-1"
    assert response.json()["products"][0]["qs"]["sku"] == ["ABC"]
