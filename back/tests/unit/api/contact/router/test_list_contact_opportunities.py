from fastapi.testclient import TestClient

from src.api.contact.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if "FROM opportunity_participant" in query:
            return [
                {
                    "id": "opp-1",
                    "name": "Deal",
                    "stage": "NEW_LEAD",
                    "role": "decision_maker",
                }
            ]
        return []


def test_list_contact_opportunities_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get('/api/contact/c-1/opportunities')

    assert response.status_code == 200
    assert response.json() == [
        {
            'id': 'opp-1',
            'name': 'Deal',
            'stage': 'NEW_LEAD',
            'role': 'decision_maker',
        }
    ]