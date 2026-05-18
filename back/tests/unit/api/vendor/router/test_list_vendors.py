from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.vendor.router import get_db


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM vendor v" in query
        return [
            {
                "id": "v-1",
                "name": "ACME",
                "email": None,
                "phone": None,
                "website": None,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "brand_count": 2,
                "family_count": 4,
                "product_count": 7,
            }
        ]


def test_list_vendors_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/vendor")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "v-1"
