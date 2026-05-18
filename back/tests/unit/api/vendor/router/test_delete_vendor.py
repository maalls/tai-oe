from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.vendor.router import get_db


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert "DELETE FROM vendor" in query
        return [{"id": "v-1"}]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_delete_vendor_returns_deleted_id():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.delete("/api/vendor/v-1")

    assert response.status_code == 200
    assert response.json()["id"] == "v-1"


def test_delete_vendor_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.delete("/api/vendor/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vendor not found"
