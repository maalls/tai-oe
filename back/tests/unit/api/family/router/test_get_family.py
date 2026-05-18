from fastapi.testclient import TestClient

from src.api.family.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert params == ('f-1',)
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


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_get_family_returns_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.get('/api/family/f-1')

    assert response.status_code == 200
    assert response.json()['id'] == 'f-1'
    assert response.json()['code'] == 'FA-01'


def test_get_family_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.get('/api/family/missing')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Family not found'