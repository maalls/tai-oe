"""Tests for ProductService.upsert_product."""

import pytest

from service.product.service import ProductService


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, table, db):
        self.table = table
        self.db = db
        self.filters = []
        self.insert_payload = None

    def select(self, _fields):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def execute(self):
        filters = dict(self.filters)
        if self.table == "brand":
            brand_id = filters.get("id")
            if brand_id:
                return _Response([row for row in self.db.brands if row.get("id") == brand_id])
            marque = filters.get("marque")
            if marque is not None:
                return _Response([row for row in self.db.brands if row.get("marque") == marque])
            name = filters.get("name")
            return _Response([row for row in self.db.brands if row.get("name") == name])
        if self.table == "product" and self.insert_payload is None:
            sku = filters.get("sku")
            return _Response([row for row in self.db.products if row.get("sku") == sku])
        if self.table == "product" and self.insert_payload is not None:
            created = {"id": "p-new", **self.insert_payload}
            self.db.products.append(created)
            return _Response([created])
        raise AssertionError("Unexpected query")


class _Supabase:
    def __init__(self):
        self.brands = [{"id": "b-1", "marque": "ABB", "name": "ABB"}]
        self.products = []

    def from_(self, table):
        return _Query(table, self)


def test_upsert_product_requires_fields():
    service = ProductService(supabase=_Supabase())

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
    supabase = _Supabase()
    service = ProductService(supabase=supabase)

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
    supabase = _Supabase()
    service = ProductService(supabase=supabase)

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
    supabase = _Supabase()
    service = ProductService(supabase=supabase)

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
