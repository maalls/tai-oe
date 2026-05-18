import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_product_service
from src.api.main import create_app


class _FakeProductService:
    def update_product(self, product_id: str, payload: dict):
        return {"id": product_id, "payload": payload}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_product_service] = lambda: _FakeProductService()
    return TestClient(app)


def test_product_update_returns_payload():
    client = _client()

    response = client.put(
        "/api/products/p-1",
        json={
            "marque": "Brand",
            "refciale": "SKU-1",
            "libelle240": "Prod",
            "tarif": 12.5,
            "family_codes": ["A"],
            "vector_text": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["product"]["id"] == "p-1"
