import unittest
from src.api.product.handler import ProductController
from src.infrastructure.clients.supabase import get_supabase_service

class TestQuoteController(unittest.TestCase):

    def setUp(self):
        self.supabase = get_supabase_service()
        # Clean up any test products that might exist from previous test runs

    def _resolve_brand_id(self):
        brands = self.supabase.from_('brand').select('id').eq('marque', 'ABB').limit(1).execute()
        if not brands.data:
            self.skipTest("Brand ABB not found in database")
        return brands.data[0]['id']
        

    def test_get(self):
        controller = ProductController()
        brand_id = self._resolve_brand_id()
        # Insert a test product directly into the database for retrieval
        test_product = {
            "sku": "TESTSKU123",
            "name": "Test Product",
            "price": 99.99,
            "brand_id": brand_id,
        }
        tp = self.supabase.from_('product').select('*').eq('sku', test_product['sku']).execute();
        if len(tp.data) > 0:
            print("Test product already exists in database, skipping insert")
        else:
            self.supabase.from_('product').upsert(test_product).execute()

        # Test listing products without filters
        products = controller.list({'sku': [test_product['sku']]})
        assert len(products) > 0, "No products returned from list endpoint"
        self.assertTrue(any(p['sku'] == "TESTSKU123" for p in products), "Inserted product not found in list without filters")

        # Test listing products with SKU filter
        products_filtered = controller.list({'sku': ['TESTSKU123']})
        self.assertTrue(any(p['sku'] == "TESTSKU123" for p in products_filtered), "Inserted product not found in list with SKU filter")

    def test_post_returns_expected_json(self):
        controller = ProductController()
        self._resolve_brand_id()
        payload = {
            "family_codes": ["NET_PRICE"],
            "libelle240": "Test Product",
            "marque": "ABB",
            "refciale": "TYUUYUYUYUYUYUYUYUYUYUY",
            "tarif": 123.45,
            "vector_text": "Test Product",
        }
        product = controller.post(payload)

        assert "id" in product
        assert product["sku"] == payload["refciale"]
        assert product["name"] == payload["libelle240"]
        assert product["price"] == payload["tarif"]

        products = self.supabase.from_('product').select('*').eq('sku', payload['refciale']).execute()
        assert len(products.data) > 0, "Product not found in database after insertion"
        db_product = products.data[0]
        assert db_product["sku"] == payload["refciale"]
        assert db_product["name"] == payload["libelle240"]
        assert db_product["price"] == payload["tarif"]
        


if __name__ == "__main__":
    unittest.main()
