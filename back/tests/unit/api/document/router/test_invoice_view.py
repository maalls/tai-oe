import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.document.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if "FROM document" in query and "type = 'INVOICE'" in query:
            if params == ("missing", "opp-1"):
                return []
            assert params == ("inv-1", "opp-1")
            return [
                {
                    "id": "inv-1",
                    "opportunity_id": "opp-1",
                    "type": "INVOICE",
                    "status": "SENT",
                }
            ]
        if "FROM sent_email" in query:
            assert params == ("inv-1",)
            return [
                {
                    "id": "sent-1",
                    "document_id": "inv-1",
                    "subject": "Invoice sent",
                }
            ]
        if "JOIN contact" in query:
            assert params == ("opp-1",)
            return [
                {
                    "id": "contact-1",
                    "account_id": "acc-1",
                    "email": "buyer@example.com",
                }
            ]
        raise AssertionError("Unexpected query")


def test_invoice_view_requires_opportunity_id():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/invoice/inv-1/view")

    assert response.status_code == 400
    assert response.json()["error"] == "Missing opportunity_id"


def test_invoice_view_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/invoice/missing/view?opportunity_id=opp-1")

    assert response.status_code == 404
    assert response.json()["error"] == "Invoice not found"


def test_invoice_view_returns_aggregated_payload():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/invoice/inv-1/view?opportunity_id=opp-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["invoice"]["id"] == "inv-1"
    assert payload["sent_email"]["id"] == "sent-1"
    assert payload["default_contact"]["id"] == "contact-1"
