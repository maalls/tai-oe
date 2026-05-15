"""Unit tests for RfqHandlers.handle_rfq_generate."""

from pathlib import Path

from src.api.business.rfq_handler import RfqHandlers


class _EmailServiceStub:
    def __init__(self, email):
        self.email = email
        self.calls = []

    def get_email(self, email_id: str):
        self.calls.append(email_id)
        if isinstance(self.email, Exception):
            raise self.email
        return self.email


class _ServiceFactoryStub:
    def __init__(self, email_service):
        self.email_service = email_service

    def create_email_service(self):
        return self.email_service


class _EmailRepositoryStub:
    class _DbHandler:
        def __init__(self, email):
            self.email = email
            self.calls = []

        def get_email(self, email_id: str):
            self.calls.append(email_id)
            return self.email

    def __init__(self, email):
        self.db_handler = self._DbHandler(email)

    @staticmethod
    def _clean_email_body(text: str, max_length: int = 3000):
        return text[:max_length]


def test_load_email_content_prefers_ddd_email_body():
    email_service = _EmailServiceStub(type("Email", (), {"body": "full body"})())
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(email_service),
        email_repository=_EmailRepositoryStub({"body_full": "legacy full", "body_preview": "legacy preview"}),
    )

    content = handler._load_email_content("e-1")

    assert content == "full body"
    assert email_service.calls == ["e-1"]
    assert handler.email_repository.db_handler.calls == []


def test_load_email_content_falls_back_to_legacy_preview_when_ddd_body_empty():
    email_service = _EmailServiceStub(type("Email", (), {"body": None})())
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(email_service),
        email_repository=_EmailRepositoryStub({"body_full": None, "body_preview": "preview body"}),
    )

    content = handler._load_email_content("e-2")

    assert content == "preview body"
    assert email_service.calls == ["e-2"]
    assert handler.email_repository.db_handler.calls == ["e-2"]


def test_handle_rfq_generate_uses_loaded_email_content(monkeypatch):
    email_service = _EmailServiceStub(type("Email", (), {"body": "rfq content"})())
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(email_service),
        email_repository=_EmailRepositoryStub(None),
    )

    monkeypatch.setattr(
        "src.api.business.rfq_handler.extract_rfp_from_text",
        lambda content, timeout_seconds=300: {"content": content, "timeout_seconds": timeout_seconds},
    )

    result = handler.handle_rfq_generate(message_id="e-3", user_id="u-1")

    assert result["status"] == "ok"
    assert result["draft"] == {"content": "rfq content", "timeout_seconds": 300}


def test_handle_rfq_generate_returns_error_when_no_content_available():
    email_service = _EmailServiceStub(type("Email", (), {"body": None})())
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(email_service),
        email_repository=_EmailRepositoryStub(None),
    )

    result = handler.handle_rfq_generate(message_id="e-4", user_id="u-1")

    assert result["status"] == "error"
    assert "no text provided" in result["message"].lower()


class _Response:
    def __init__(self, data):
        self.data = data


class _TableQuery:
    def __init__(self, table_name, supabase):
        self.table_name = table_name
        self.supabase = supabase
        self.filters = []
        self.payload = None

    def select(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.payload = payload
        return self

    def update(self, payload):
        self.payload = payload
        return self

    def execute(self):
        return self.supabase.execute(self.table_name, self.filters, self.payload)


class _SupabaseStub:
    def __init__(self):
        self.operations = []

    def table(self, table_name):
        return _TableQuery(table_name, self)

    def execute(self, table_name, filters, payload):
        self.operations.append((table_name, list(filters), payload))
        if table_name == "account":
            if payload is None:
                if filters == [("name", "ACME")]:
                    return _Response([])
                return _Response([{"id": "acc-1", "name": "ACME"}])
            return _Response([{"id": "acc-1"}])
        if table_name == "contact" and payload is None:
            return _Response([])
        if table_name == "contact" and payload is not None:
            return _Response([{"id": "contact-1"}])
        if table_name == "opportunity" and payload and "source_reference_id" not in payload:
            return _Response([{"id": "opp-1"}])
        if table_name == "opportunity" and payload and "source_reference_id" in payload:
            return _Response([{"id": "opp-1", "source_reference_id": payload["source_reference_id"]}])
        if table_name == "opportunity" and payload is None and filters == [("id", "opp-1")]:
            return _Response({"account_id": "acc-1"})
        if table_name == "opportunity_participant":
            return _Response([{"id": "participant-1"}])
        if table_name == "document":
            return _Response([{"id": "doc-1"}])
        return _Response([])


class _OpportunityRepositoryStub:
    def _extract_and_enrich_rfp_data(self, text):
        return {"title": "Imported RFP", "contact": {"company_name": "ACME"}}

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None, pre_extracted_data=None):
        return {
            "status": "ok",
            "opportunity_id": opportunity_id,
            "content": content,
            "pre_extracted_data": pre_extracted_data,
        }

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        return {"status": "ok", "opportunity_id": opportunity_id}


def test_handle_create_opportunity_from_rfp_returns_error_without_message_or_file():
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(_EmailServiceStub(type("Email", (), {"body": None})())),
        email_repository=_EmailRepositoryStub(None),
        opportunity_repository=_OpportunityRepositoryStub(),
        supabase=_SupabaseStub(),
    )

    result = handler.handle_create_opportunity_from_rfp(
        body=b"--x\r\nContent-Disposition: form-data; name=\"message\"\r\n\r\n\r\n--x--\r\n",
        content_type="multipart/form-data; boundary=x",
        user_id="u-1",
    )

    assert result["status"] == "error"
    assert "message text or attachment" in result["message"].lower()


def test_handle_create_opportunity_from_rfp_creates_opportunity_and_document(tmp_path, monkeypatch):
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(_EmailServiceStub(type("Email", (), {"body": None})())),
        email_repository=_EmailRepositoryStub(None),
        opportunity_repository=_OpportunityRepositoryStub(),
        supabase=_SupabaseStub(),
    )
    monkeypatch.setattr(handler, "_get_storage_dir", lambda _source: Path(tmp_path))
    monkeypatch.setattr("src.api.business.rfq_handler.extract_company_from_text", lambda _text: {"company_name": "ACME"})

    body = (
        b"--x\r\n"
        b"Content-Disposition: form-data; name=\"message\"\r\n\r\n"
        b"Need pricing\r\n"
        b"--x--\r\n"
    )

    result = handler.handle_create_opportunity_from_rfp(
        body=body,
        content_type="multipart/form-data; boundary=x",
        user_id="u-1",
    )

    assert result["status"] == "ok"
    assert result["opportunity"] == {
        "id": "opp-1",
        "name": "Imported RFP",
        "stage": "RFP_IN_PROGRESS",
        "document_id": "doc-1",
    }
    assert (tmp_path / next(p.name for p in tmp_path.iterdir() if p.name.endswith("_message.txt"))).exists()


def test_handle_create_rfq_source_from_html_body_creates_document_and_quote(tmp_path, monkeypatch):
    handler = RfqHandlers(
        service_factory=_ServiceFactoryStub(_EmailServiceStub(type("Email", (), {"body": None})())),
        email_repository=_EmailRepositoryStub(None),
        opportunity_repository=_OpportunityRepositoryStub(),
        supabase=_SupabaseStub(),
    )
    monkeypatch.setattr(handler, "_get_storage_dir", lambda _source: Path(tmp_path))
    monkeypatch.setattr(
        "src.api.business.rfq_handler.extract_company_from_text",
        lambda _text: {"company_name": "ACME", "email": "buyer@example.com"},
    )
    monkeypatch.setattr(
        "src.api.business.rfq_handler.pick_best_rfp_source",
        lambda picker_text, pdf_candidates: {
            "source": "text",
            "product_count": 1,
            "content": picker_text,
            "extracted_data": {"products": [{"sku": "SKU-1"}], "contact": {"company_name": "ACME"}},
        },
    )

    body = (
        b"--x\r\n"
        b"Content-Disposition: form-data; name=\"message\"\r\n\r\n"
        b"Need pricing\r\n"
        b"--x\r\n"
        b"Content-Disposition: form-data; name=\"opportunity_name\"\r\n\r\n"
        b"RFQ Alpha\r\n"
        b"--x--\r\n"
    )

    result = handler.handle_create_rfq_source_from_html_body(
        opportunity_id="opp-1",
        body=body,
        content_type="multipart/form-data; boundary=x",
        user_id="u-1",
    )

    assert result["status"] == "ok"
    assert result["message"] == "RFQ source created successfully"
    assert result["opportunity_id"] == "opp-1"
    assert result["document_id"] == "doc-1"
    assert result["quote"]["status"] == "ok"