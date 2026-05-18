from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.vendor.router import get_db


class _FakeDbOk:
    def __init__(self):
        self.calls = 0

    def execute_dict_query(self, query, params=None):
        self.calls += 1
        if self.calls == 1:
            assert "UPDATE vendor" in query
            return [
                {
                    "id": "v-1",
                    "name": "ACME Updated",
                    "email": None,
                    "phone": None,
                    "website": None,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-02T00:00:00+00:00",
                }
            ]
        return [{"brand_count": 2, "family_count": 3, "product_count": 4}]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_update_vendor_returns_updated_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put("/api/vendor/v-1", json={"name": "ACME Updated"})

    assert response.status_code == 200
    assert response.json()["name"] == "ACME Updated"
    assert response.json()["brand_count"] == 2


def test_update_vendor_returns_400_when_payload_empty():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put("/api/vendor/v-1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


def test_update_vendor_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.put("/api/vendor/missing", json={"name": "X"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Vendor not found"
