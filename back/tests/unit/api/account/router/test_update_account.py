from fastapi.testclient import TestClient

from src.api.account.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert "UPDATE account" in query
        set_part = query.split("RETURNING", 1)[0]
        assert "phone" not in set_part
        assert "website" not in set_part
        assert "industry" not in set_part
        assert "NULL::text AS phone" in query
        return [
            {
                "id": "acc-1",
                "name": "Acme Updated",
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


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_update_account_returns_updated_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put("/api/account/acc-1", json={"name": "Acme Updated"})

    assert response.status_code == 200
    assert response.json()["name"] == "Acme Updated"


def test_update_account_returns_400_when_payload_empty():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.put("/api/account/acc-1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


def test_update_account_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.put("/api/account/missing", json={"name": "X"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"
