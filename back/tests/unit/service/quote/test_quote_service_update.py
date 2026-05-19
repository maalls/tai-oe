"""Tests for QuoteService.update."""

import pytest

from service.quote.service import QuoteService


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, db, table):
        self.db = db
        self.table = table
        self.mode = None
        self.payload = None
        self.filters = {}
        self.single_mode = False

    def update(self, payload):
        self.mode = "update"
        self.payload = payload
        return self

    def delete(self):
        self.mode = "delete"
        return self

    def insert(self, payload):
        self.mode = "insert"
        self.payload = payload
        return self

    def select(self, _fields):
        self.mode = "select"
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def single(self):
        self.single_mode = True
        return self

    def limit(self, _count):
        return self

    def execute(self):
        if self.table == "document" and self.mode == "update":
            document_id = self.filters["id"]
            self.db.document[document_id].update(self.payload)
            return _Response([self.db.document[document_id]])

        if self.table == "document_line" and self.mode == "delete":
            document_id = self.filters["document_id"]
            self.db.document_lines[document_id] = []
            return _Response([])

        if self.table == "document_line" and self.mode == "insert":
            document_id = self.payload[0]["document_id"] if self.payload else None
            if document_id:
                self.db.document_lines[document_id] = list(self.payload)
            return _Response(self.payload)

        if self.table == "document" and self.mode == "select":
            document_id = self.filters["id"]
            data = {
                **self.db.document[document_id],
                "document_line": self.db.document_lines.get(document_id, []),
            }
            return _Response(data)

        if self.table == "product" and self.mode == "select":
            sku = self.filters.get("sku")
            product = self.db.products_by_sku.get(sku)
            return _Response([product] if product else [])

        raise AssertionError(f"Unsupported query: {self.table} {self.mode}")


class _Supabase:
    def __init__(self):
        self.document = {
            "d-1": {
                "id": "d-1",
                "title": "Old",
                "currency": "EUR",
                "total_excl_tax": 0,
                "total_tax": 0,
                "total_incl_tax": 0,
            }
        }
        self.document_lines = {"d-1": [{"id": "old-line", "document_id": "d-1"}]}
        self.products_by_sku = {}

    def table(self, table_name):
        return _Query(self, table_name)


def test_update_replaces_lines_and_recomputes_totals():
    supabase = _Supabase()
    service = QuoteService(supabase=supabase, opportunity_repository=object())

    payload = {
        "title": "Updated quote",
        "currency": "CHF",
        "document_line": [
            {
                "description": "Line 1",
                "quantity": 2,
                "unit_price_excl_tax": 100,
                "tax_rate": 20,
                "sku": "SKU-1",
                "brand": "ABB",
                "unit": "pcs",
                "discount_rate": 5,
                "client_discount_rate": 10,
            },
            {
                "description": "Line 2",
                "quantity": 1,
                "unit_price_excl_tax": 50,
                "tax_rate": 10,
                "sku": "SKU-2",
                "brand": "ABB",
                "unit": "pcs",
                "discount_rate": 0,
            },
        ],
    }

    result = service.update("d-1", payload)

    assert result["title"] == "Updated quote"
    assert result["currency"] == "CHF"
    assert result["total_excl_tax"] == 230.0
    assert result["total_tax"] == 41.0
    assert result["total_incl_tax"] == 271.0
    assert len(result["document_line"]) == 2


def test_update_raises_when_brand_is_not_string():
    supabase = _Supabase()
    service = QuoteService(supabase=supabase, opportunity_repository=object())

    payload = {
        "title": "Updated quote",
        "currency": "CHF",
        "document_line": [
            {
                "description": "Line 1",
                "quantity": 1,
                "unit_price_excl_tax": 10,
                "tax_rate": 20,
                "brand": {"id": "b-1"},
            }
        ],
    }

    with pytest.raises(ValueError, match="Brand must be a string"):
        service.update("d-1", payload)


