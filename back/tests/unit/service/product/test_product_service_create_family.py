"""Tests for ProductService.create_family."""

from service.product.service import ProductService


class _DbHandler:
    def __init__(self):
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return [{"id": "f-1", "brand_id": params[0], "code": params[1], "type": params[2]}]


def test_create_family_sets_brand_and_code():
    db_handler = _DbHandler()
    service = ProductService(db_handler=db_handler)

    family = service.create_family("NET_PRICE", "b-1")

    assert family["id"] == "f-1"
    assert family["brand_id"] == "b-1"
    assert family["code"] == "NET_PRICE"
    assert family["type"] == "NET_PRICE"
    assert "INSERT INTO family" in db_handler.calls[0][0]
