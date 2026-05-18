import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_product_service
from src.api_fastapi.main import create_app


class _FakeProductService:
    def get_product_by_id(self, product_id: str):
        if product_id == "missing":
            return None
        return {
            "id": product_id,
            "sku": "SKU-1",
            "name": "Prod",
            "price": 10,
            "vector_text": "vec",
            "brand": {"name": "Brand"},
            "product_family": [{"family": {"code": "A"}}, {"family": {"code": "B"}}],
        }


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_product_service] = lambda: _FakeProductService()
    return TestClient(app)


def test_product_get_returns_front_shape():
    client = _client()

    response = client.get("/api/products/p-1")

    assert response.status_code == 200
    assert response.json()["marque"] == "Brand"
    assert response.json()["refciale"] == "SKU-1"
    assert response.json()["family_codes"] == ["A", "B"]


def test_product_get_not_found():
    client = _client()

    response = client.get("/api/products/missing")

    assert response.status_code == 404
