import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_database_repository
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if "FROM document_line" in query:
            assert params == ("doc-1",)
            return [
                {
                    "id": "line-1",
                    "document_id": "doc-1",
                    "position": 1,
                    "description": "Line 1",
                }
            ]
        if params == ("doc-1", "opp-1"):
            return [
                {
                    "id": "doc-1",
                    "opportunity_id": "opp-1",
                    "type": "QUOTE",
                    "status": "DRAFT",
                    "title": "Quote 1",
                }
            ]
        return []


def test_document_get_requires_opportunity_id():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/document/doc-1")

    assert response.status_code == 400
    assert response.json()["error"] == "Missing opportunity_id"


def test_document_get_returns_404_when_missing():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/document/missing?opportunity_id=opp-1")

    assert response.status_code == 404
    assert response.json()["error"] == "Document not found"


def test_document_get_returns_row():
    app = create_app()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/document/doc-1?opportunity_id=opp-1")

    assert response.status_code == 200
    assert response.json()["id"] == "doc-1"
    assert len(response.json()["document_line"]) == 1