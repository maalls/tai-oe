from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.vendor.router import get_db


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM brand b" in query
        assert params == ("v-1",)
        return [
            {
                "id": "b-1",
                "name": "Brand A",
                "marque": "Brand A",
                "website": None,
                "target_margin": 20,
                "minimum_margin": 10,
                "product_count": 3,
            }
        ]


def test_list_vendor_brands_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/vendor/v-1/brands")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "b-1"
    assert body[0]["product_count"] == 3
