import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.document.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM document" in query
        assert "type = 'INVOICE'" in query
        assert params == ("opp-1",)
        return [
            {
                "id": "inv-1",
                "opportunity_id": "opp-1",
                "type": "INVOICE",
                "status": "DRAFT",
            }
        ]


def test_invoice_list_requires_opportunity_id():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/invoice")

    assert response.status_code == 400
    assert response.json()["error"] == "Missing opportunity_id"


def test_invoice_list_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/invoice?opportunity_id=opp-1")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "inv-1"
