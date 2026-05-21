from decimal import Decimal

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.product.router import get_db


class _FakeDb:
    def __init__(self):
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        if "FROM product p" in query:
            return [
                {
                    "id": "p-1",
                    "sku": "SKU-1",
                    "name": "Produit 1",
                    "price": 100,
                    "brand_id": "b-1",
                    "brand_ref_id": "b-1",
                    "brand_name": "Acme",
                    "brand_marque": "ACME",
                    "brand_minimum_margin": 10,
                    "brand_target_margin": 15,
                    "family_id": "f-1",
                    "family_name": "Remise",
                    "family_code": "DISC",
                    "family_type": "discount",
                    "family_discount": 12,
                    "family_minimum_margin": 5,
                    "family_target_margin": 9,
                    "family_quantity": 1,
                    "family_net_price": None,
                    "family_product_code": None,
                }
            ]
        return [
            {
                "id": "np-1",
                "name": "Net Price",
                "code": "NP",
                "type": "net_price",
                "product_code": "SKU-1",
                "quantity": 1,
                "discount": None,
                "minimum_margin": 5,
                "target_margin": 8,
                "net_price": 72,
            }
        ]


def test_products_quote_context_returns_grouped_payload():
    fake_db = _FakeDb()
    app = create_app()
    app.dependency_overrides[get_db] = lambda: fake_db
    client = TestClient(app)

    response = client.get("/api/products/quote-context", params=[("sku", "SKU-1"), ("sku", "SKU-2")])

    assert response.status_code == 200
    assert response.json() == {
        "products": [
            {
                "id": "p-1",
                "sku": "SKU-1",
                "name": "Produit 1",
                "price": 100,
                "batch": None,
                "brand_id": "b-1",
                "brand": {
                    "id": "b-1",
                    "name": "Acme",
                    "marque": "ACME",
                    "minimum_margin": 10,
                    "target_margin": 15,
                },
                "product_family": [
                    {
                        "family": {
                            "id": "f-1",
                            "name": "Remise",
                            "code": "DISC",
                            "type": "discount",
                            "discount": 12,
                            "minimum_margin": 5,
                            "target_margin": 9,
                            "quantity": 1,
                            "net_price": None,
                            "product_code": None,
                        }
                    }
                ],
            }
        ],
        "net_price_families": [
            {
                "id": "np-1",
                "name": "Net Price",
                "code": "NP",
                "type": "net_price",
                "product_code": "SKU-1",
                "quantity": 1,
                "discount": None,
                "minimum_margin": 5,
                "target_margin": 8,
                "net_price": 72,
            }
        ],
    }
    assert fake_db.calls[0][1] == ("SKU-1", "SKU-2")
    assert fake_db.calls[1][1] == ("SKU-1", "SKU-2")


def test_products_quote_context_returns_empty_payload_without_skus():
    class _UnusedDb:
        def execute_dict_query(self, query, params=None):
            raise AssertionError("db should not be called")

    app = create_app()
    app.dependency_overrides[get_db] = lambda: _UnusedDb()
    client = TestClient(app)

    response = client.get("/api/products/quote-context")

    assert response.status_code == 200
    assert response.json() == {"products": [], "net_price_families": []}


def test_products_quote_context_serializes_decimal_values():
    class _DecimalDb:
        def execute_dict_query(self, query, params=None):
            if "FROM product p" in query:
                return [
                    {
                        "id": "p-2",
                        "sku": "SKU-DEC",
                        "name": "Produit Decimal",
                        "price": Decimal("100.50"),
                        "brand_id": "b-2",
                        "brand_ref_id": "b-2",
                        "brand_name": "Decimal Brand",
                        "brand_marque": "DB",
                        "brand_minimum_margin": Decimal("10.25"),
                        "brand_target_margin": Decimal("15.75"),
                        "family_id": None,
                        "family_name": None,
                        "family_code": None,
                        "family_type": None,
                        "family_discount": None,
                        "family_minimum_margin": None,
                        "family_target_margin": None,
                        "family_quantity": None,
                        "family_net_price": None,
                        "family_product_code": None,
                    }
                ]

            return [
                {
                    "id": "np-dec",
                    "name": "Net Price Decimal",
                    "code": "NPD",
                    "type": "net_price",
                    "product_code": "SKU-DEC",
                    "quantity": 1,
                    "discount": None,
                    "minimum_margin": Decimal("5.50"),
                    "target_margin": Decimal("8.25"),
                    "net_price": Decimal("72.35"),
                }
            ]

    app = create_app()
    app.dependency_overrides[get_db] = lambda: _DecimalDb()
    client = TestClient(app)

    response = client.get("/api/products/quote-context", params=[("sku", "SKU-DEC")])

    assert response.status_code == 200
    body = response.json()
    assert body["products"][0]["price"] == 100.5
    assert body["products"][0]["brand"]["minimum_margin"] == 10.25
    assert body["net_price_families"][0]["net_price"] == 72.35