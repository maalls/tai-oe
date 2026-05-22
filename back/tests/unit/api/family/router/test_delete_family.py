from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDb:
    def __init__(self):
        self.queries = []

    def execute_dict_query(self, query, params=None):
        self.queries.append((query, params))
        if query.startswith('DELETE FROM family'):
            return [{'id': 'f-1'}]
        return []


def test_delete_family_returns_id():
    fake_db = _FakeDb()
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: fake_db
    client = TestClient(app)

    response = client.delete('/api/family/f-1')

    assert response.status_code == 200
    assert response.json()['id'] == 'f-1'
    assert fake_db.queries[0][0].startswith('DELETE FROM product_family')
    assert fake_db.queries[1][0].startswith('DELETE FROM family')