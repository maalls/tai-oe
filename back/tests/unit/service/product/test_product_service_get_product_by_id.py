"""Tests for ProductService.get_product_by_id."""

from service.product.service import ProductService


class _DbHandler:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return [self.row]


def test_get_product_by_id_selects_media_relation():
    db_handler = _DbHandler({"id": "p-1"})
    service = ProductService(db_handler=db_handler)

    result = service.get_product_by_id("p-1")

    assert result == {"id": "p-1"}
    assert len(db_handler.calls) == 1
    assert "product_media" in db_handler.calls[0][0]
    assert db_handler.calls[0][1] == ("p-1",)