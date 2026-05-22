from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert params == ("acc-1",)
        return [{"id": "acc-1"}]


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_delete_account_returns_deleted_id():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.delete("/api/account/acc-1")

    assert response.status_code == 200
    assert response.json()["id"] == "acc-1"


def test_delete_account_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.delete("/api/account/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"
