"""Tests for ProductService.upsert_product."""

import pytest

from service.product.service import ProductService


class _DbHandler:
    def __init__(self):
        self.brands = [{"id": "b-1", "marque": "ABB", "name": "ABB"}]
        self.products = []
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        if "FROM brand WHERE id" in query:
            return [row for row in self.brands if row.get("id") == params[0]]
        if "FROM brand WHERE marque" in query:
            return [row for row in self.brands if row.get("marque") == params[0]]
        if "FROM brand WHERE name" in query:
            return [row for row in self.brands if row.get("name") == params[0]]
        if "SELECT * FROM product WHERE sku" in query:
            return [row for row in self.products if row.get("sku") == params[0]]
        if "INSERT INTO product" in query:
            created = {
                "id": "p-new",
                "sku": params[0],
                "name": params[1],
                "brand_id": params[2],
                "price": params[3],
                "batch": params[4],
            }
            self.products.append(created)
            return [created]
        raise AssertionError(f"Unexpected query: {query}")


def test_upsert_product_requires_fields():
    service = ProductService(db_handler=_DbHandler())

    with pytest.raises(ValueError, match="Missing product field: vector_text"):
        service.upsert_product(
            {
                "family_codes": ["NET_PRICE"],
                "libelle240": "Name",
                "marque": "ABB",
                "refciale": "SKU",
                "tarif": 1.2,
            }
        )


def test_upsert_product_inserts_and_attaches_brand():
    db_handler = _DbHandler()
    service = ProductService(db_handler=db_handler)

    result = service.upsert_product(
        {
            "batch": 3,
            "family_codes": ["NET_PRICE"],
            "libelle240": "Name",
            "marque": "ABB",
            "refciale": "SKU-1",
            "tarif": 12.5,
            "vector_text": "Name",
        }
    )

    assert result["id"] == "p-new"
    assert result["sku"] == "SKU-1"
    assert result["brand"]["id"] == "b-1"
    assert result["batch"] == 3


def test_upsert_product_prefers_brand_id_when_provided():
    db_handler = _DbHandler()
    service = ProductService(db_handler=db_handler)

    result = service.upsert_product(
        {
            "brand_id": "b-1",
            "family_codes": [],
            "libelle240": "Name",
            "marque": "Wrong label",
            "refciale": "SKU-2",
            "tarif": 12.5,
            "vector_text": "Name",
        }
    )

    assert result["brand"]["id"] == "b-1"


def test_upsert_product_defaults_batch_to_one_when_missing():
    db_handler = _DbHandler()
    service = ProductService(db_handler=db_handler)

    result = service.upsert_product(
        {
            "family_codes": [],
            "libelle240": "Name",
            "marque": "ABB",
            "refciale": "SKU-3",
            "tarif": 12.5,
            "vector_text": "Name",
        }
    )

    assert result["batch"] == 1
