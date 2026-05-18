from fastapi.testclient import TestClient

from src.api.contact.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert params == ("c-1",)
        return [{"id": "c-1"}]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_delete_contact_returns_deleted_id():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.delete("/api/contact/c-1")

    assert response.status_code == 200
    assert response.json()["id"] == "c-1"


def test_delete_contact_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.delete("/api/contact/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"
