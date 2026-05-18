import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_product_service
from src.api_fastapi.main import create_app


class _FakeProductService:
    def post_product(self, payload: dict):
        return {"id": "p-1", "payload": payload}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_product_service] = lambda: _FakeProductService()
    return TestClient(app)


def test_products_create_returns_payload():
    client = _client()

    response = client.post(
        "/api/products",
        json={
            "marque": "Brand",
            "refciale": "SKU-1",
            "libelle240": "Prod",
            "tarif": 12.5,
            "family_codes": ["A"],
            "vector_text": "",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "ok"
    assert response.json()["product"]["id"] == "p-1"
