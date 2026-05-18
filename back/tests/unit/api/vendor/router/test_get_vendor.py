from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.vendor.router import get_db


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert "WHERE v.id = %s" in query
        assert "COUNT(DISTINCT pf.product_id)" in query
        return [
            {
                "id": "v-1",
                "name": "ACME",
                "email": "hello@acme.com",
                "phone": None,
                "website": None,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "brand_count": 1,
                "family_count": 1,
                "product_count": 1,
            }
        ]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_get_vendor_returns_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.get("/api/vendor/v-1")

    assert response.status_code == 200
    assert response.json()["name"] == "ACME"


def test_get_vendor_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.get("/api/vendor/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vendor not found"
