
"""Email classification request handler."""

from typing import Dict

from src.api.routes.server_body_helpers import read_json
from src.service.product.service import ProductService


class ProductController:
    def update_line_from_product(self, document: Dict, product: Dict) -> None:
        """Met à jour une ligne de document à partir d'un produit."""
        print(f"[ProductController][update_line_from_product] Updating line from product: {product}")

        response = self.product_service.supabase.table("document_line").select("*").eq("id", product.get("id")).single().execute()
        if not response.data:
            line = {
                "document_id": document.get("id"),
            }
        else:
            line = response.data
        line['description'] = product.get("description")
        line['position'] = product.get("position")
        line["sku"] = product.get("sku")
        line['quantity'] = product.get("quantity")
        line['unit'] = product.get("unit")
        line['unit_price'] = product.get("price")
        line['unit_price_excl_tax'] = product.get("price")
        line['tax_rate'] = product.get("tax_rate", 20)
        line['discount_rate'] = product.get("discount_rate", 0)
        line['line_total_excl_tax'] = round(float(product.get("quantity", 1) or 1) * float(product.get("price", 0) or 0), 2)

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


def handle_products_post(handler):
    """Handle /api/products POST endpoint."""
    payload = read_json(handler, default={})
    controller = ProductController()
    result = {"status": "ok", "product": controller.post(payload)}
    return handler.json(result, 201)


def handle_products_get(handler, qs):
    """Handle /api/products GET endpoint."""
    controller = ProductController()
    return handler.json({"products": controller.list(qs)})
