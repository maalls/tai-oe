from fastapi.testclient import TestClient

from src.api.brand.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert params == ('b-1',)
        return [
            {
                'id': 'b-1',
                'name': 'Brand A',
                'vendor_id': 'v-1',
                'website': None,
                'email': None,
                'phone': None,
                'minimum_margin': 10,
                'target_margin': 20,
                'created_at': '2026-01-01T00:00:00+00:00',
                'updated_at': '2026-01-01T00:00:00+00:00',
            }
        ]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_get_brand_returns_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.get('/api/brand/b-1')

    assert response.status_code == 200
    assert response.json()['id'] == 'b-1'
    assert response.json()['vendor_id'] == 'v-1'


def test_get_brand_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.get('/api/brand/missing')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Brand not found'
