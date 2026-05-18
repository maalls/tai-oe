from fastapi.testclient import TestClient

from src.api.contact.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert "UPDATE contact" in query
        return [
            {
                "id": "c-1",
                "account_id": "acc-1",
                "name": "Jane Updated",
                "email": "jane@example.com",
                "phone": None,
                "role_title": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_update_contact_returns_updated_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put("/api/contact/c-1", json={"name": "Jane Updated"})

    assert response.status_code == 200
    assert response.json()["name"] == "Jane Updated"


def test_update_contact_returns_400_when_payload_empty():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put("/api/contact/c-1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


def test_update_contact_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.put("/api/contact/missing", json={"name": "X"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"
