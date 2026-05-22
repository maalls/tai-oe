from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert params == ("c-1",)
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


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_get_contact_returns_row():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.get("/api/contact/c-1")

    assert response.status_code == 200
    assert response.json()["id"] == "c-1"


def test_get_contact_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.get("/api/contact/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"
