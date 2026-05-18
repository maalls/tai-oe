from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_auth_service
from src.api.opportunity.router import get_db


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeDbCreateContact:
    def execute_dict_query(self, query, params=None):
        if "SELECT id, account_id FROM opportunity" in query:
            return [{"id": "opp-1", "account_id": "a-1"}]
        if "FROM contact" in query and "LIMIT 1" in query:
            return []
        if "INSERT INTO contact" in query:
            return [{"id": "c-1"}]
        if "FROM opportunity_participant" in query and "LIMIT 1" in query:
            return []
        return []


class _FakeDbExistingContact:
    def execute_dict_query(self, query, params=None):
        if "SELECT id, account_id FROM opportunity" in query:
            return [{"id": "opp-1", "account_id": "a-1"}]
        if "FROM contact" in query and "LIMIT 1" in query:
            return [{"id": "c-1"}]
        if "FROM opportunity_participant" in query and "LIMIT 1" in query:
            return [{"opportunity_id": "opp-1", "contact_id": "c-1"}]
        return []


class _FakeDbMissingOpp:
    def execute_dict_query(self, query, params=None):
        if "SELECT id, account_id FROM opportunity" in query:
            return []
        return []


def _client(db) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_extract_author_contact_requires_auth():
    client = _client(_FakeDbCreateContact())

    response = client.post(
        "/api/opportunity/opp-1/extract-author-contact",
        json={"from_email": "alice@example.com", "from_name": "Alice"},
    )

    assert response.status_code == 401


def test_extract_author_contact_creates_contact_and_links():
    client = _client(_FakeDbCreateContact())

    response = client.post(
        "/api/opportunity/opp-1/extract-author-contact",
        json={"from_email": "alice@example.com", "from_name": "Alice"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["contact_id"] == "c-1"
    assert response.json()["linked"] is True


def test_extract_author_contact_uses_existing_contact_and_link():
    client = _client(_FakeDbExistingContact())

    response = client.post(
        "/api/opportunity/opp-1/extract-author-contact",
        json={"from_email": "alice@example.com", "from_name": "Alice"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["contact_id"] == "c-1"


def test_extract_author_contact_returns_404_when_missing_opportunity():
    client = _client(_FakeDbMissingOpp())

    response = client.post(
        "/api/opportunity/missing/extract-author-contact",
        json={"from_email": "alice@example.com", "from_name": "Alice"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found"