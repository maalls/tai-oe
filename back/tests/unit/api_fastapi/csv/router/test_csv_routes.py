import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_database_repository, get_file_handler
from src.api_fastapi.main import create_app


class _FakeFileHandler:
    storage_dir = None

    def __init__(self):
        from pathlib import Path

        self.storage_dir = Path("/tmp/fake-storage")
        self.csv_reader = self

    def handle_uploaded_file(self, filename: str, file_data: bytes):
        if not filename.endswith((".csv", ".xls", ".xlsx")):
            raise ValueError("Invalid file type. Allowed: ('.xlsx', '.xls', '.csv')")
        return {"status": "ok", "source": filename, "size": len(file_data)}

    def list_sources(self):
        return ["source-a.xlsx", "source-b.xls"]

    def list_files_for_source(self, source: str):
        return [f"{source}-sheet.csv"]

    def safe_file_from_query(self, source: str, sheet: str):
        class _FakePath:
            def read_bytes(self_inner):
                return f"{source}:{sheet}".encode()

        return _FakePath()

    def read_source_file(self, source: str):
        return f"{source}:{source}".encode()

    def read(self, target, offset: int, limit: int, filters=None):
        return {
            "rows": [{"target": target.read_bytes().decode(), "offset": offset, "limit": limit, "filters": filters}],
            "columns": ["target", "offset", "limit", "filters"],
        }


class _FakeDatabaseRepository:
    def query_table(self, table: str, columns_raw: str, where_clause: str, sort_by: str, limit: int, offset: int):
        return [{"table": table, "limit": limit, "offset": offset, "sort_by": sort_by, "where": where_clause}]

    def list_public_tables_with_columns(self):
        return [
            {
                "table_name": "products",
                "column_name": "id",
                "data_type": "uuid",
                "is_nullable": "NO",
                "column_default": None,
                "character_maximum_length": None,
                "numeric_precision": None,
                "numeric_scale": None,
            }
        ]


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_file_handler] = lambda: _FakeFileHandler()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepository()
    return TestClient(app)


def test_csv_sources_returns_payload():
    client = _client()

    response = client.get("/api/csv/sources")

    assert response.status_code == 200
    assert response.json() == ["source-a.xlsx", "source-b.xls"]


def test_csv_files_returns_payload():
    client = _client()

    response = client.get("/api/csv/files?source=source-a.xlsx")

    assert response.status_code == 200
    assert response.json()["files"] == ["source-a.xlsx-sheet.csv"]


def test_csv_preview_returns_payload():
    client = _client()

    response = client.get("/api/csv/preview?source=source-a.xlsx&file=sheet-1.csv&limit=10&offset=2")

    assert response.status_code == 200
    assert response.json()["rows"][0]["target"] == "source-a.xlsx:sheet-1.csv"
    assert response.json()["rows"][0]["limit"] == 10
    assert response.json()["rows"][0]["offset"] == 2


def test_csv_source_download_returns_attachment():
    client = _client()

    response = client.get("/api/csv/source?source=source-a.xlsx")

    assert response.status_code == 200
    assert response.content == b"source-a.xlsx:source-a.xlsx"
    assert 'attachment; filename="source-a.xlsx"' == response.headers["content-disposition"]


def test_csv_raw_returns_attachment_without_source():
    client = _client()

    response = client.get("/api/csv/raw?file=sheet-1.csv")

    assert response.status_code == 200
    assert response.content == b":sheet-1.csv"
    assert 'attachment; filename="sheet-1.csv"' == response.headers["content-disposition"]


def test_csv_query_returns_payload():
    client = _client()

    response = client.get("/api/csv/query?table=products&limit=10&offset=5&sortBy=name%20ASC")

    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"][0]["table"] == "products"
    assert payload["rows"][0]["limit"] == 10
    assert payload["rows"][0]["offset"] == 5


def test_csv_query_tables_returns_payload():
    client = _client()

    response = client.get("/api/csv/query?tables=1")

    assert response.status_code == 200
    assert response.json()["tables"][0]["name"] == "products"


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
