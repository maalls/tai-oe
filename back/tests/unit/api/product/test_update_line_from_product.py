
import unittest
from src.api.product.handler import ProductController

class DummySingle:
    def __init__(self, data=None):
        self.data = data
    def execute(self):
        return self

class DummyTable:
    def __init__(self, data=None):
        self._data = data
        self._id = None
    def select(self, *_):
        return self
    def eq(self, key, value):
        self._id = value
        return self
    def single(self):
        return DummySingle(self._data)

class DummySupabase:
    def __init__(self, data=None):
        self._data = data
    def table(self, name):
        return DummyTable(self._data)

class DummyProductService:
    def __init__(self, supabase=None):
        self.supabase = supabase or DummySupabase()

class TestUpdateLineFromProduct(unittest.TestCase):
    def setUp(self):
        # Inject dummy supabase
        self.controller = ProductController(product_service=DummyProductService(DummySupabase()))

    def test_update_line_from_product(self):
        document = {"id": "doc-1"}
        product = {
            "id": "prod-1",
            "description": "desc",
            "position": 1,
            "sku": "SKU1",
            "quantity": 2,
            "unit": "U",
            "price": 10.0,
            "tax_rate": 20,
            "discount_rate": 0
        }
        try:
            self.controller.update_line_from_product(document, product)
        except Exception as e:
            self.fail(f"update_line_from_product raised: {e}")
