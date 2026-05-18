import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api_fastapi.dependencies import get_auth_service, get_quote_send_service
from src.api_fastapi.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-1"}
        return False, None


def _client(monkeypatch) -> TestClient:
    from src.api_fastapi.quote import router as quote_router_module

    class _FakeQuoteController:
        def update(self, document_id: str, payload: dict, user_id: str | None = None):
            return {"status": "ok", "document_id": document_id, "payload": payload, "user_id": user_id}

        def handle_quote_submit(self, payload):
            return {"status": "ok", "payload": payload, "pdf_filename": "quote_1.pdf"}

        def handle_list_quotes(self):
            return {"status": "ok", "quotes": ["quote_1.pdf"], "total": 1}

        def handle_generate_quote_pdf(self, document_id: str, user_id: str | None = None):
            return {"status": "ok", "document_id": document_id, "user_id": user_id}

        def handle_get_quote_file(self, filename: str):
            if filename == "missing.pdf":
                raise FileNotFoundError("missing")
            return b"%PDF-1.4\n"

    monkeypatch.setattr(quote_router_module, "Quote", _FakeQuoteController)

    class _FakeQuoteSendService:
        def handle_quote_send(self, body: bytes, content_type: str):
            del body, content_type
            return {"status": "ok", "message": "sent"}

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_quote_send_service] = lambda: _FakeQuoteSendService()
    return TestClient(app)


def test_quote_update_requires_auth(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote/doc-1", json={"title": "x"})

    assert response.status_code == 401


def test_quote_update_returns_payload(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote/doc-1", headers={"Authorization": "Bearer valid"}, json={"title": "x"})

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-1"


def test_quote_generate_pdf_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote/doc-2/pdf", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc-2"


def test_quote_download_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.get("/api/quotes/download/file.pdf?inline=1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")


def test_quote_download_not_found(monkeypatch):
    client = _client(monkeypatch)

    response = client.get("/api/quotes/download/missing.pdf")

    assert response.status_code == 404


def test_quote_submit_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote", json={"products": [{"sku": "A"}]})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_quote_send_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post(
        "/api/quote/send",
        json={"pdf_filename": "quote_1.pdf", "email": "test@example.com", "body": "hello"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_quotes_list_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.get("/api/quotes/list")

    assert response.status_code == 200
    assert response.json()["total"] == 1
