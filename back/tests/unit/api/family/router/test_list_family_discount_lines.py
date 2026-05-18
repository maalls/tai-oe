from fastapi.testclient import TestClient

from src.api.family.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if 'SELECT f.id AS family_id' in query:
            return [{'family_id': 'f-1', 'document_id': 'd-1'}]
        if 'FROM document_line' in query:
            assert params == ('d-1',)
            return [
                {
                    'id': 'l-1',
                    'position': 1,
                    'quantity': 2,
                    'unit': 'U',
                    'unit_price_excl_tax': 10,
                    'discount_rate': 5,
                    'sku': 'SKU-1',
                    'line_total_excl_tax': 19,
                }
            ]
        return []


class _FakeDbNoDoc:
    def execute_dict_query(self, query, params=None):
        if 'SELECT f.id AS family_id' in query:
            return [{'family_id': 'f-1', 'document_id': None}]
        return []


def test_list_family_discount_lines_returns_document_and_lines():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get('/api/family/f-1/discount-lines')

    assert response.status_code == 200
    body = response.json()
    assert body['document_id'] == 'd-1'
    assert len(body['lines']) == 1
    assert body['lines'][0]['id'] == 'l-1'


def test_list_family_discount_lines_returns_empty_when_document_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbNoDoc()
    client = TestClient(app)

    response = client.get('/api/family/f-1/discount-lines')

    assert response.status_code == 200
    body = response.json()
    assert body['document_id'] is None
    assert body['lines'] == []