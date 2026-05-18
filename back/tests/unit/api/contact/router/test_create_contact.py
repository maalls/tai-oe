from fastapi.testclient import TestClient

from src.api.contact.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "INSERT INTO contact" in query
        assert params[0] == "acc-1"
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


def test_create_contact_returns_created_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.post(
        "/api/contact",
        json={"account_id": "acc-1", "name": "Jane", "email": "jane@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Jane"
