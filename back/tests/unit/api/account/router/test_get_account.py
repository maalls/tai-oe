from fastapi.testclient import TestClient

from src.api.account.router import get_db
from src.api.main import create_app


class _FakeDbOk:
    def execute_dict_query(self, query, params=None):
        assert params == ("acc-1",)
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


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        return []


def test_get_account_returns_row():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbOk()
    client = TestClient(app)

    response = client.get("/api/account/acc-1")

    assert response.status_code == 200
    assert response.json()["id"] == "acc-1"


def test_get_account_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.get("/api/account/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"
