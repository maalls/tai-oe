from fastapi.testclient import TestClient

from src.api.catalog.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM brand" in query
        assert "vendor_id" in query
        return [
            {
                "id": "b-1",
                "name": "Brand A",
                "vendor_id": "v-1",
                "website": None,
                "email": None,
                "phone": None,
                "minimum_margin": 10,
                "target_margin": 20,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]


def test_list_catalog_brands_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/catalog/brands")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "b-1"
    assert response.json()[0]["vendor_id"] == "v-1"
