from fastapi.testclient import TestClient

from src.api.family.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if query.strip().startswith('UPDATE family'):
            assert params[-1] == 'f-1'
            return [
                {
                    'id': 'f-1',
                    'name': 'Family A',
                    'code': 'FA-01',
                    'type': 'net_price',
                    'brand_id': 'b-1',
                    'product_code': 'SKU-1',
                    'quantity': 1,
                    'discount': 10,
                    'minimum_margin': 0,
                    'target_margin': 0,
                    'unit': 'U',
                    'packing': None,
                    'lead_time_week': None,
                    'net_price': 9.5,
                    'created_at': '2026-01-01T00:00:00+00:00',
                    'updated_at': '2026-01-01T00:00:00+00:00',
                }
            ]
        if 'FROM product' in query:
            return [
                {
                    'id': 'p-1',
                    'sku': 'SKU-1',
                    'name': 'Product 1',
                    'price': 12.5,
                    'brand_id': 'b-1',
                }
            ]
        return []


def test_update_family_returns_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.put(
        '/api/family/f-1',
        json={'name': 'Family A', 'type': 'net_price', 'product_code': 'SKU-1'},
    )

    assert response.status_code == 200
    assert response.json()['id'] == 'f-1'
    assert response.json()['product_code'] == 'SKU-1'


def test_update_family_returns_400_when_empty_payload():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.put('/api/family/f-1', json={})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No fields to update'