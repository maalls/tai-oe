from fastapi.testclient import TestClient

from src.api.brand.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        if query.strip().startswith('UPDATE brand'):
            assert params[0] == 'Brand A Updated'
            return [
                {
                    'id': 'b-1',
                    'name': 'Brand A Updated',
                    'vendor_id': 'v-1',
                    'website': None,
                    'email': None,
                    'phone': None,
                    'minimum_margin': 11,
                    'target_margin': 21,
                    'created_at': '2026-01-01T00:00:00+00:00',
                    'updated_at': '2026-01-02T00:00:00+00:00',
                }
            ]
        raise AssertionError('Unexpected query')


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_update_brand_returns_updated_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put('/api/brand/b-1', json={'name': 'Brand A Updated'})

    assert response.status_code == 200
    assert response.json()['name'] == 'Brand A Updated'


def test_update_brand_returns_400_when_payload_empty():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put('/api/brand/b-1', json={})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No fields to update'


def test_update_brand_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.put('/api/brand/missing', json={'name': 'X'})

    assert response.status_code == 404
    assert response.json()['detail'] == 'Brand not found'
