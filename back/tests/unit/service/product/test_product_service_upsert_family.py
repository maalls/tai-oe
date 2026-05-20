"""Tests for ProductService.upsert_family."""

import pytest

from service.product.service import ProductService


class _Response:
    def __init__(self, data):
        self.data = data


class _FamilySelectQuery:
    def __init__(self, db):
        self.db = db
        self.filters = {}

    def select(self, _fields):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def in_(self, key, values):
        self.filters[key] = list(values)
        return self

    def execute(self):
        brand_id = self.filters.get("brand_id")
        codes = set(self.filters.get("code", []))
        rows = [f for f in self.db.families if f["brand_id"] == brand_id and f["code"] in codes]
        return _Response(rows)


class _FamilyInsertQuery:
    def __init__(self, db):
        self.db = db
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        raise AssertionError("Family insert should not be called")


class _ProductFamilyUpsertQuery:
    def __init__(self, db):
        self.db = db
        self.payload = None

    def upsert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        self.db.links.append(self.payload)
        return _Response([self.payload])


class _Supabase:
    def __init__(self):
        self.families = [{"id": "f-existing", "brand_id": "b-1", "code": "A", "name": "A", "type": "NET_PRICE"}]
        self.links = []

    def from_(self, table):
        if table == "family":
            return _FamilyTable(self)
        if table == "product_family":
            return _ProductFamilyUpsertQuery(self)
        raise AssertionError("Unexpected table")


class _FamilyTable:
    def __init__(self, db):
        self.db = db
        self._mode = "select"
        self._selector = _FamilySelectQuery(db)
        self._inserter = _FamilyInsertQuery(db)

    def select(self, fields):
        self._mode = "select"
        return self._selector.select(fields)

    def insert(self, payload):
        self._mode = "insert"
        return self._inserter.insert(payload)


def test_upsert_family_rejects_unknown_family_codes():
    supabase = _Supabase()
    service = ProductService(supabase=supabase)
    product = {"id": "p-1", "brand_id": "b-1"}

    with pytest.raises(ValueError, match="Unknown family code"):
        service.upsert_family(product, {"family_codes": ["A", "B"]})


def test_upsert_family_links_existing_codes_only():
    supabase = _Supabase()
    supabase.families.append({"id": "f-2", "brand_id": "b-1", "code": "B", "name": "B", "type": "NET_PRICE"})
    service = ProductService(supabase=supabase)
    product = {"id": "p-1", "brand_id": "b-1"}

    result = service.upsert_family(product, {"family_codes": ["A", "B"]})

    assert len(result["families"]) == 2
    assert {f["code"] for f in result["families"]} == {"A", "B"}
    assert len(supabase.links) == 2
