from fastapi.testclient import TestClient

from src.api.contact.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM contact" in query
        return [
            {
                "id": "c-1",
                "account_id": "acc-1",
                "name": "Jane",
                "email": "jane@example.com",
                "phone": None,
                "role_title": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]


def test_list_contacts_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/contact")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "c-1"
