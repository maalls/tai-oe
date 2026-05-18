from fastapi.testclient import TestClient

from src.api.family.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if query.startswith('DELETE FROM family'):
            return [{'id': 'f-1'}]
        return []


def test_delete_family_returns_id():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.delete('/api/family/f-1')

    assert response.status_code == 200
    assert response.json()['id'] == 'f-1'