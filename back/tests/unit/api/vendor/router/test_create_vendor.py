from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_database_repository


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "INSERT INTO vendor" in query
        return [
            {
                "id": "v-1",
                "name": "ACME",
                "email": "hello@acme.com",
                "phone": None,
                "website": None,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "brand_count": 0,
                "family_count": 0,
                "product_count": 0,
            }
        ]


def test_create_vendor_returns_created_row():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.post("/api/vendor", json={"name": "ACME", "email": "hello@acme.com"})

    assert response.status_code == 200
    assert response.json()["id"] == "v-1"
