from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_database_repository


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if "FROM document" in query:
            assert params == ("opp-1",)
            return [{"id": "doc-1"}]
        if "FROM sent_email" in query:
            assert params == ("doc-1",)
            return [
                {
                    "id": "mail-1",
                    "document_id": "doc-1",
                    "subject": "Quote sent",
                    "to_emails": ["client@example.com"],
                }
            ]
        return []


class _FakeDbNoQuote:
    def execute_dict_query(self, query, params=None):
        if "FROM document" in query:
            return []
        return []


class _FakeDbNoEmail:
    def execute_dict_query(self, query, params=None):
        if "FROM sent_email" in query:
            return []
        return []


def test_get_opportunity_sent_email_from_latest_quote():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-1/sent-email")

    assert response.status_code == 200
    assert response.json()["sent_email"]["id"] == "mail-1"


def test_get_opportunity_sent_email_with_document_id():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-1/sent-email?document_id=doc-1")

    assert response.status_code == 200
    assert response.json()["sent_email"]["document_id"] == "doc-1"


def test_get_opportunity_sent_email_returns_null_without_quote():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNoQuote()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-1/sent-email")

    assert response.status_code == 200
    assert response.json()["sent_email"] is None


def test_get_opportunity_sent_email_returns_null_without_sent_email():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbNoEmail()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-1/sent-email?document_id=doc-1")

    assert response.status_code == 200
    assert response.json()["sent_email"] is None