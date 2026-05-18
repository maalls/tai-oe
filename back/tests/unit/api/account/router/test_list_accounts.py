from fastapi.testclient import TestClient

from src.api.account.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "FROM account" in query
        assert "NULL::text AS phone" in query
        assert "NULL::text AS website" in query
        assert "NULL::text AS industry" in query
        return [
            {
                "id": "acc-1",
                "name": "Acme",
                "vat_number": "FR123",
                "siret": "123",
                "address_line1": None,
                "address_line2": None,
                "postal_code": None,
                "city": "Paris",
                "country_code": "FR",
                "payment_terms_default": None,
                "phone": None,
                "website": None,
                "industry": None,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        ]


def test_list_accounts_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/account")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "acc-1"
