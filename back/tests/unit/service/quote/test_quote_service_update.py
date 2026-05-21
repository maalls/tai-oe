"""Tests for QuoteService.update."""

from contextlib import contextmanager
from copy import deepcopy

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


class _Cursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        compact_query = " ".join(query.split()).upper()

        if compact_query.startswith("UPDATE DOCUMENT"):
            title, currency, total_excl_tax, total_tax, total_incl_tax, document_id = params
            self.connection.pending_document[document_id].update({
                "title": title,
                "currency": currency,
                "total_excl_tax": total_excl_tax,
                "total_tax": total_tax,
                "total_incl_tax": total_incl_tax,
            })
            return

        if compact_query.startswith("DELETE FROM DOCUMENT_LINE"):
            document_id = params[0]
            self.connection.pending_document_lines[document_id] = []
            return

        raise AssertionError(f"Unsupported query: {compact_query}")

    def executemany(self, query, rows):
        if self.connection.fail_on_insert:
            raise RuntimeError("Insert failure")

        compact_query = " ".join(query.split()).upper()
        if not compact_query.startswith("INSERT INTO DOCUMENT_LINE"):
            raise AssertionError(f"Unsupported bulk query: {compact_query}")

        for row in rows:
            (
                line_id,
                document_id,
                position,
                description,
                quantity,
                unit_price_excl_tax,
                tax_rate,
                sku,
                brand,
                unit,
                discount_rate,
                client_discount_rate,
                line_total_excl_tax,
            ) = row
            self.connection.pending_document_lines.setdefault(document_id, []).append({
                "id": line_id,
                "document_id": document_id,
                "position": position,
                "description": description,
                "quantity": quantity,
                "unit_price_excl_tax": unit_price_excl_tax,
                "tax_rate": tax_rate,
                "sku": sku,
                "brand": brand,
                "unit": unit,
                "discount_rate": discount_rate,
                "client_discount_rate": client_discount_rate,
                "line_total_excl_tax": line_total_excl_tax,
            })


class _Connection:
    def __init__(self, db, fail_on_insert=False):
        self.db = db
        self.fail_on_insert = fail_on_insert
        self.pending_document = deepcopy(db.document)
        self.pending_document_lines = deepcopy(db.document_lines)

    def cursor(self):
        return _Cursor(self)

    def apply(self):
        self.db.document = self.pending_document
        self.db.document_lines = self.pending_document_lines


class _DbHandler:
    def __init__(self, db, fail_on_insert=False):
        self.db = db
        self.fail_on_insert = fail_on_insert

    @contextmanager
    def get_connection(self):
        conn = _Connection(self.db, fail_on_insert=self.fail_on_insert)
        try:
            yield conn
            conn.apply()
        except Exception:
            raise


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
    db_handler = _DbHandler(supabase)
    service = QuoteService(supabase=supabase, opportunity_repository=object(), db_handler=db_handler)

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
    assert result["document_line"][1]["discount_rate"] == 0.0
    assert result["document_line"][1]["client_discount_rate"] == 0.0


def test_update_raises_when_brand_is_not_string():
    supabase = _Supabase()
    db_handler = _DbHandler(supabase)
    service = QuoteService(supabase=supabase, opportunity_repository=object(), db_handler=db_handler)

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


def test_update_preserves_existing_data_when_insert_fails_in_transaction():
    supabase = _Supabase()
    db_handler = _DbHandler(supabase, fail_on_insert=True)
    service = QuoteService(supabase=supabase, opportunity_repository=object(), db_handler=db_handler)

    payload = {
        "title": "Updated quote",
        "currency": "CHF",
        "document_line": [
            {
                "description": "Line 1",
                "quantity": 1,
                "unit_price_excl_tax": 10,
                "tax_rate": 20,
                "discount_rate": 0,
            }
        ],
    }

    with pytest.raises(RuntimeError, match="Insert failure"):
        service.update("d-1", payload)

    assert supabase.document["d-1"]["title"] == "Old"
    assert supabase.document["d-1"]["currency"] == "EUR"
    assert supabase.document_lines["d-1"] == [{"id": "old-line", "document_id": "d-1"}]


