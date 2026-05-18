from fastapi.testclient import TestClient

from src.api.catalog.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM family" in query
        return [
            {
                "id": "f-1",
                "name": "Family A",
                "type": "standard",
                "brand_id": "b-1",
            }
        ]


def test_list_catalog_families_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/catalog/families")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "f-1"
