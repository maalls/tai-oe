"""Tests for ProductService.list_products."""

from service.product.service import ProductService


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.ilike_calls = []
        self.limit_value = None

    def select(self, _fields):
        return self

    def ilike(self, field, pattern):
        self.ilike_calls.append((field, pattern))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        return _Response(self.rows)


class _Supabase:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = None

    def from_(self, table):
        assert table == "product"
        self.last_query = _Query(self.rows)
        return self.last_query


def test_list_products_applies_sku_filter_and_limit():
    supabase = _Supabase([{"sku": "ABC"}])
    service = ProductService(supabase=supabase)

    result = service.list_products({"sku": ["ABC"], "limit": ["5"]})

    assert result == [{"sku": "ABC"}]
    assert supabase.last_query.ilike_calls == [("sku", "ABC")]
    assert supabase.last_query.limit_value == 5
