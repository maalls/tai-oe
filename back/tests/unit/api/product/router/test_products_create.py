import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_product_service
from src.api.main import create_app


class _FakeProductService:
    def post_product(self, payload: dict):
        self.payload = payload
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


def test_products_create_defaults_batch_to_one():
    fake_service = _FakeProductService()

    app = create_app()
    app.dependency_overrides[get_product_service] = lambda: fake_service
    client = TestClient(app)

    response = client.post(
        "/api/products",
        json={
            "brand_id": "b-1",
            "marque": "ABB",
            "refciale": "SKU-3",
            "libelle240": "Prod",
            "tarif": 12.5,
            "family_codes": ["A"],
            "vector_text": "",
        },
    )

    assert response.status_code == 201
    assert fake_service.payload["batch"] == 1


def test_products_create_accepts_csv_family_codes():
    fake_service = _FakeProductService()

    app = create_app()
    app.dependency_overrides[get_product_service] = lambda: fake_service
    client = TestClient(app)

    response = client.post(
        "/api/products",
        json={
            "brand_id": "b-1",
            "marque": "ABB",
            "refciale": "SKU-2",
            "libelle240": "Prod",
            "tarif": 12.5,
            "family_codes": "A10, A11",
            "vector_text": "",
        },
    )

    assert response.status_code == 201
    assert fake_service.payload["family_codes"] == ["A10", "A11"]
