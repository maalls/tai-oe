"""Tests for ProductService.upsert_family."""

import pytest

from service.product.service import ProductService


class _DbHandler:
    def __init__(self):
        self.families = [{"id": "f-existing", "brand_id": "b-1", "code": "A", "name": "A", "type": "NET_PRICE"}]
        self.links = []
        self.query_calls = []

    def execute_dict_query(self, query, params=None):
        self.query_calls.append((query, params))
        if "FROM family" in query:
            brand_id = params[0]
            codes = set(params[1:])
            return [f for f in self.families if f["brand_id"] == brand_id and f["code"] in codes]
        raise AssertionError("Unexpected execute_dict_query call")

    def execute_update(self, query, params=None):
        if "INSERT INTO product_family" in query:
            self.links.append({"product_id": params[0], "family_id": params[1]})
            return 1
        raise AssertionError("Unexpected execute_update call")


def test_upsert_family_rejects_unknown_family_codes():
    db_handler = _DbHandler()
    service = ProductService(db_handler=db_handler)
    product = {"id": "p-1", "brand_id": "b-1"}

    with pytest.raises(ValueError, match="Unknown family code"):
        service.upsert_family(product, {"family_codes": ["A", "B"]})


def test_upsert_family_links_existing_codes_only():
    db_handler = _DbHandler()
    db_handler.families.append({"id": "f-2", "brand_id": "b-1", "code": "B", "name": "B", "type": "NET_PRICE"})
    service = ProductService(db_handler=db_handler)
    product = {"id": "p-1", "brand_id": "b-1"}

    result = service.upsert_family(product, {"family_codes": ["A", "B"]})

    assert len(result["families"]) == 2
    assert {f["code"] for f in result["families"]} == {"A", "B"}
    assert len(db_handler.links) == 2
