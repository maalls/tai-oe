from fastapi.testclient import TestClient

from src.api.account.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert "INSERT INTO account" in query
        insert_part = query.split("VALUES", 1)[0]
        assert "phone" not in insert_part
        assert "website" not in insert_part
        assert "industry" not in insert_part
        assert "NULL::text AS phone" in query
        assert params[0] == "Acme"
        return [
            {
                "id": "acc-1",
                "name": "Acme",
                "vat_number": None,
                "siret": None,
                "address_line1": None,
                "address_line2": None,
                "postal_code": None,
                "city": None,
                "country_code": "FR",
                "payment_terms_default": None,
                "phone": None,
                "website": None,
                "industry": None,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        ]


def test_create_account_returns_created_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.post("/api/account", json={"name": "Acme"})

    assert response.status_code == 200
    assert response.json()["name"] == "Acme"
