import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_invoice_handlers, get_quote_send_service, get_quote_service
from src.api.main import create_app


class _FakeAuthService:
    def verify_token(self, auth_header: str):
        if auth_header == "Bearer valid":
            return True, {"id": "u-1"}
        return False, None


def _client(monkeypatch) -> TestClient:
    class _FakeQuoteService:
        def update(self, document_id: str, payload: dict, user_id: str | None = None):
            return {"status": "ok", "document_id": document_id, "payload": payload, "user_id": user_id}

        def handle_quote_submit(self, payload):
            return {"status": "ok", "payload": payload, "pdf_filename": "quote_1.pdf"}

        def handle_list_quotes(self):
            return {"status": "ok", "quotes": ["quote_1.pdf"], "total": 1}

        def handle_generate_quote_pdf(self, document_id: str, user_id: str | None = None):
            return {"status": "ok", "document_id": document_id, "user_id": user_id}

        def handle_generate_quote_pdf_from_opportunity(self, opportunity_id: str, user_id: str | None = None):
            return {"status": "ok", "opportunity_id": opportunity_id, "user_id": user_id}

        def handle_get_quote_file(self, filename: str):
            if filename == "missing.pdf":
                raise FileNotFoundError("missing")
            return b"%PDF-1.4\n"

    class _FakeQuoteSendService:
        def handle_quote_send(self, body: bytes, content_type: str):
            del body, content_type
            return {"status": "ok", "message": "sent"}

    class _FakeInvoiceHandlers:
        def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str | None = None):
            return {"status": "ok", "invoice_id": "inv-1", "quote_id": quote_id, "user_id": user_id}

        def handle_generate_invoice_pdf(self, document_id: str, user_id: str | None = None):
            return {"status": "ok", "document_id": document_id, "user_id": user_id}

        def handle_send_invoice(self, invoice_id: str, payload: dict, user_id: str | None = None):
            return {"status": "ok", "invoice_id": invoice_id, "payload": payload, "user_id": user_id}

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_quote_send_service] = lambda: _FakeQuoteSendService()
    app.dependency_overrides[get_quote_service] = lambda: _FakeQuoteService()
    app.dependency_overrides[get_invoice_handlers] = lambda: _FakeInvoiceHandlers()
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


def test_quote_generate_from_opportunity_requires_auth(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote/opp-1/generate")

    assert response.status_code == 401


def test_quote_generate_from_opportunity_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote/opp-1/generate", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["opportunity_id"] == "opp-1"


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


def test_quote_invoice_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/quote/doc-9/invoice", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["quote_id"] == "doc-9"


def test_invoice_pdf_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/invoice/inv-9/pdf", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["document_id"] == "inv-9"


def test_invoice_send_route(monkeypatch):
    client = _client(monkeypatch)

    response = client.post(
        "/api/invoice/inv-9/send",
        headers={"Authorization": "Bearer valid"},
        json={"to": ["x@y.com"], "subject": "Invoice", "body": "Hi"},
    )

    assert response.status_code == 200
    assert response.json()["invoice_id"] == "inv-9"
