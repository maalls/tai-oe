import pytest
from decimal import Decimal

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_database_repository


class _FakeDb:
    def __init__(self):
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return [
            {
                "id": "p-1",
                "marque": "ACME",
                "refciale": "SKU-1",
                "libelle240": "Produit 1",
                "tarif": 42,
                "batch": 6,
                "brand_id": "b-1",
                "brand_name": "Acme",
                "family_codes": ["FAM"],
                "total_count": 3,
            }
        ]


def test_products_search_returns_payload_and_passes_filters():
    fake_db = _FakeDb()
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: fake_db
    client = TestClient(app)

    response = client.get(
        "/api/products/search",
        params={
            "query": "abc",
            "marque": "acme",
            "refciale": "sku",
            "tarif": "42",
            "family": "FAM",
            "limit": 50,
            "offset": 100,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "products": [
            {
                "id": "p-1",
                "marque": "ACME",
                "refciale": "SKU-1",
                "libelle240": "Produit 1",
                "tarif": 42,
                "batch": 6,
                "brand_id": "b-1",
                "brand_name": "Acme",
                "family_codes": ["FAM"],
            }
        ],
        "total_count": 3,
    }

    _, params = fake_db.calls[0]
    assert params == (
        "%abc%",
        "%abc%",
        "%abc%",
        "%abc%",
        "%acme%",
        "%acme%",
        "%sku%",
        "%42%",
        "FAM",
        50,
        100,
    )


def test_products_search_returns_empty_payload_when_no_rows():
    class _EmptyDb:
        def execute_dict_query(self, query, params=None):
            return []

    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _EmptyDb()
    client = TestClient(app)

    response = client.get("/api/products/search")

    assert response.status_code == 200
    assert response.json() == {"products": [], "total_count": 0}


def test_products_search_serializes_decimal_tarif_values():
    class _DecimalDb:
        def execute_dict_query(self, query, params=None):
            return [
                {
                    "id": "p-dec",
                    "marque": "ACME",
                    "refciale": "EXS07MSC3K",
                    "libelle240": "Produit Decimal",
                    "tarif": Decimal("42.50"),
                    "brand_id": "b-1",
                    "brand_name": "Acme",
                    "family_codes": [],
                    "total_count": 1,
                }
            ]

    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _DecimalDb()
    client = TestClient(app)

    response = client.get(
        "/api/products/search",
        params={
            "refciale": "EXS07MSC3K",
            "exact_match": "true",
            "limit": 500,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    assert response.json()["products"][0]["tarif"] == 42.5