import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_file_handler
from src.api_fastapi.main import create_app


class _FakeFileHandler:
    def handle_uploaded_file(self, filename: str, file_data: bytes):
        if not filename.endswith((".csv", ".xls", ".xlsx")):
            raise ValueError("Invalid file type. Allowed: ('.xlsx', '.xls', '.csv')")
        return {"status": "ok", "source": filename, "size": len(file_data)}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_file_handler] = lambda: _FakeFileHandler()
    return TestClient(app)


def test_csv_source_upload_returns_payload():
    client = _client()

    response = client.post(
        "/api/csv/source",
        files={"file": ("sample.csv", b"name,value\na,1", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["source"] == "sample.csv"


def test_csv_source_upload_rejects_invalid_extension():
    client = _client()

    response = client.post(
        "/api/csv/source",
        files={"file": ("sample.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["error"]
