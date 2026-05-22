from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert 'INSERT INTO brand' in query
        assert params[0] == 'Brand A'
        assert params[7] == 'v-1'
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


def test_create_brand_returns_created_row():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.post(
        '/api/brand',
        json={'name': 'Brand A', 'vendor_id': 'v-1', 'minimum_margin': 10, 'target_margin': 20},
    )

    assert response.status_code == 200
    assert response.json()['id'] == 'b-1'
