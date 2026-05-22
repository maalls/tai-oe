from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert params[3] == 'b-1'
        return [
            {
                'id': 'f-1',
                'name': 'Family A',
                'code': 'FA-01',
                'type': 'discount',
                'brand_id': 'b-1',
                'product_code': None,
                'quantity': 1,
                'discount': 10,
                'minimum_margin': 0,
                'target_margin': 0,
                'unit': 'U',
                'packing': None,
                'lead_time_week': None,
                'net_price': None,
                'created_at': '2026-01-01T00:00:00+00:00',
                'updated_at': '2026-01-01T00:00:00+00:00',
            }
        ]


def test_create_family_returns_row():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.post(
        '/api/family',
        json={'name': 'Family A', 'code': 'FA-01', 'type': 'discount', 'brand_id': 'b-1'},
    )

    assert response.status_code == 200
    assert response.json()['id'] == 'f-1'
    assert response.json()['brand_id'] == 'b-1'