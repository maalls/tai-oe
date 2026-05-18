import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.document.router import get_db
from src.api.main import create_app


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        assert params == ("opp-1",)
        return [
            {
                "id": "doc-1",
                "type": "QUOTE",
                "status": "DRAFT",
                "title": "Quote 1",
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]


def test_document_list_requires_opportunity_id():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/document")

    assert response.status_code == 400
    assert response.json()["error"] == "Missing opportunity_id"


def test_document_list_returns_rows():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/document?opportunity_id=opp-1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "doc-1"