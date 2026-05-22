from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDb:
    def __init__(self):
        self.updated = False
        self.inserted = False

    def execute_dict_query(self, query, params=None):
        if 'SELECT f.id AS family_id' in query:
            return [{'family_id': 'f-1', 'document_id': 'd-1'}]
        if query.strip().startswith('UPDATE document_line'):
            self.updated = True
            return []
        if query.strip().startswith('INSERT INTO document_line'):
            self.inserted = True
            return []
        if 'FROM document_line' in query:
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


def test_save_family_discount_lines_updates_and_inserts():
    fake_db = _FakeDb()
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: fake_db
    client = TestClient(app)

    response = client.put(
        '/api/family/f-1/discount-lines',
        json={
            'lines': [
                {
                    'id': 'l-1',
                    'position': 1,
                    'sku': 'SKU-1',
                    'quantity': 2,
                    'unit': 'U',
                    'unit_price_excl_tax': 10,
                    'discount_rate': 5,
                    'line_total_excl_tax': 19,
                },
                {
                    'id': 'new-1',
                    'position': 2,
                    'sku': 'SKU-2',
                    'quantity': 1,
                    'unit': 'U',
                    'unit_price_excl_tax': 12,
                    'discount_rate': 0,
                    'line_total_excl_tax': 12,
                },
            ]
        },
    )

    assert response.status_code == 200
    assert fake_db.updated is True
    assert fake_db.inserted is True
    assert response.json()['document_id'] == 'd-1'


def test_save_family_discount_lines_returns_400_when_document_missing():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNoDoc()
    client = TestClient(app)

    response = client.put('/api/family/f-1/discount-lines', json={'lines': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No FAMILY_DISCOUNT document found for this family'