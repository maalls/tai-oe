"""Tests for ProductService.create_family."""

from service.product.service import ProductService


class _Response:
    def __init__(self, data):
        self.data = data


class _FamilyInsertQuery:
    def __init__(self):
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        return _Response([{"id": "f-1", **self.payload}])


class _Supabase:
    def __init__(self):
        self.query = _FamilyInsertQuery()

    def from_(self, table):
        assert table == "family"
        return self.query


def test_create_family_sets_brand_and_code():
    supabase = _Supabase()
    service = ProductService(supabase=supabase)

    family = service.create_family("NET_PRICE", "b-1")

    assert family["id"] == "f-1"
    assert family["brand_id"] == "b-1"
    assert family["code"] == "NET_PRICE"
    assert family["type"] == "NET_PRICE"
