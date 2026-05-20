import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_db
from src.api.main import create_app


class _FakeDB:
    def __init__(self):
        self.queries = []

    def execute_dict_query(self, query: str, params=None):
        self.queries.append((query, params))
        if query.startswith("DELETE FROM product WHERE id = %s"):
            if params == ("p-1",):
                return [{"id": "p-1"}]
            return []
        return []

    def execute_update(self, query: str, params=None):
        self.queries.append((query, params))
        return 1


def _client(fake_db: _FakeDB) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: fake_db
    return TestClient(app)


def test_product_delete_deletes_product_and_links():
    fake_db = _FakeDB()
    client = _client(fake_db)

    response = client.delete("/api/products/p-1")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["id"] == "p-1"
    assert fake_db.queries[0][0].startswith("DELETE FROM product_family")
    assert fake_db.queries[1][0].startswith("DELETE FROM product WHERE id = %s")


def test_product_delete_returns_404_when_missing():
    fake_db = _FakeDB()
    client = _client(fake_db)

    response = client.delete("/api/products/does-not-exist")

    assert response.status_code == 404
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "Product not found"
