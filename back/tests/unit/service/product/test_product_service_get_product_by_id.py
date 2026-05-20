"""Tests for ProductService.get_product_by_id."""

from service.product.service import ProductService


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, data):
        self.data = data
        self.select_fields = None
        self.eq_calls = []
        self.maybe_single_called = False

    def select(self, fields):
        self.select_fields = fields
        return self

    def eq(self, field, value):
        self.eq_calls.append((field, value))
        return self

    def maybe_single(self):
        self.maybe_single_called = True
        return self

    def execute(self):
        return _Response(self.data)


class _Supabase:
    def __init__(self, data):
        self.data = data
        self.last_query = None

    def from_(self, table):
        assert table == "product"
        self.last_query = _Query(self.data)
        return self.last_query


def test_get_product_by_id_selects_media_relation():
    supabase = _Supabase({"id": "p-1"})
    service = ProductService(supabase=supabase)

    result = service.get_product_by_id("p-1")

    assert result == {"id": "p-1"}
    assert supabase.last_query.select_fields == "*,brand(*),product_family(*,family(*)),product_media(*)"
    assert supabase.last_query.eq_calls == [("id", "p-1")]
    assert supabase.last_query.maybe_single_called is True