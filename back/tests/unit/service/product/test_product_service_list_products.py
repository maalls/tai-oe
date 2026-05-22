"""Tests for ProductService.list_products."""

from service.product.service import ProductService


class _DbHandler:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return self.rows


def test_list_products_applies_sku_filter_and_limit():
    db_handler = _DbHandler([{"sku": "ABC"}])
    service = ProductService(db_handler=db_handler)

    result = service.list_products({"sku": ["ABC"], "limit": ["5"]})

    assert result == [{"sku": "ABC"}]
    assert len(db_handler.calls) == 1
    assert "FROM product p" in db_handler.calls[0][0]
    assert db_handler.calls[0][1] == ("ABC%", 5)
