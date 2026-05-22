from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_database_repository


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if "FROM opportunity" in query:
            return [
                {
                    "id": "opp-1",
                    "source": "email",
                    "source_reference_id": "em-1",
                }
            ]
        if "FROM opportunity_participant" in query:
            return [
                {
                    "role": "from",
                    "contact_id": "c-1",
                    "contact_id_ref": "c-1",
                    "contact_name": "John",
                    "contact_email": "john@example.com",
                }
            ]
        if "FROM email WHERE" in query:
            return [{"id": "em-1", "subject": "Test"}]
        if "FROM email_attachment" in query:
            return [{"id": "a-1", "filename": "x.pdf", "mime_type": "application/pdf", "size": 10}]
        return []


class _FakeDbDocSource:
    def execute_dict_query(self, query, params=None):
        if "FROM opportunity" in query:
            return [
                {
                    "id": "opp-2",
                    "source": "rfp_upload",
                    "source_reference_id": "doc-1",
                }
            ]
        if "FROM opportunity_participant" in query:
            return []
        if "FROM document WHERE id" in query:
            return [{"id": "doc-1", "storage_key": "documents/doc-1.pdf"}]
        if "WHERE opportunity_id = %s" in query and "type = 'ATTACHMENT'" in query:
            return [{"id": "doc-att-1", "title": "Attachment: offer.pdf", "storage_key": "k1"}]
        return []


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        if "FROM opportunity" in query:
            return []
        return []


def test_get_opportunity_source_email_payload():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-1/source")

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "email"
    assert body["email"]["id"] == "em-1"
    assert len(body["participants"]) == 1
    assert len(body["attachments"]) == 1


def test_get_opportunity_source_document_payload():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbDocSource()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-2/source")

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "rfp_upload"
    assert body["document"]["id"] == "doc-1"
    assert len(body["attachments"]) == 1


def test_get_opportunity_source_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDbMissing()
    client = TestClient(app)

    response = client.get("/api/opportunity/missing/source")

    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found"