from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert 'FROM family f' in query
        assert params == ('b-1',)
        return [
            {
                'id': 'f-1',
                'name': 'Family A',
                'code': 'FAM-A',
                'type': 'standard',
                'brand_id': 'b-1',
                'product_code': 'SKU-1',
                'quantity': 1,
                'discount': 5,
                'minimum_margin': 10,
                'target_margin': 20,
                'unit': 'pcs',
                'packing': 'box',
                'lead_time_week': 2,
                'net_price': 12.3,
                'product_family_count': 3,
                'product_id': 'p-1',
                'product_sku': 'SKU-1',
                'product_name': 'Product A',
                'product_price': 45.0,
                'product_brand_id': 'b-1',
            }
        ]


def test_list_brand_families_returns_rows():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get('/api/brand/b-1/families')

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]['id'] == 'f-1'
    assert body[0]['product_family_count'] == 3
    assert body[0]['product']['id'] == 'p-1'
