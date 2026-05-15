"""Email classification request handler."""

from typing import Dict

from src.service.product.service import ProductService


class ProductController:

    def __init__(self, product_service: ProductService = None):
        self.product_service = product_service or ProductService()

    def list(self, qs: dict):
        return self.product_service.list_products(qs)

    def post(self, payload) -> Dict:
        return self.product_service.post_product(payload)

    def upsert_family(self, product, payload):
        return self.product_service.upsert_family(product, payload)

    def create_family(self, code, brand_id):
        return self.product_service.create_family(code, brand_id)

    def upsert_product(self, payload) -> Dict:
        """
        {
            "marque": "Hélita",
            "refciale": "sdf",
            "libelle240": "sdf",
            "tarif": 1,
            "family_codes": [
                "FA",
                "BU"
            ],
            "vector_text": ""
        }
        """
        return self.product_service.upsert_product(payload)
