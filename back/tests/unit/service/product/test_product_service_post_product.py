"""Tests for ProductService.post_product."""

from service.product.service import ProductService


class _ServiceSpy(ProductService):
    def __init__(self):
        pass

    def upsert_product(self, payload):
        self.upsert_payload = payload
        return {"id": "p-1", "brand_id": "b-1"}

    def upsert_family(self, product, payload):
        self.family_call = (product, payload)
        product["families"] = [{"id": "f-1", "code": "NET_PRICE"}]
        return product


def test_post_product_orchestrates_upsert_and_family_linking():
    service = _ServiceSpy()
    payload = {"family_codes": ["NET_PRICE"]}

    result = service.post_product(payload)

    assert service.upsert_payload == payload
    assert service.family_call[0]["id"] == "p-1"
    assert result["families"][0]["code"] == "NET_PRICE"
