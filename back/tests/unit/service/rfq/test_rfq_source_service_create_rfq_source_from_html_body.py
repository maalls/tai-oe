"""Tests for RfqSourceService.create_rfq_source_from_html_body."""

import importlib

from service.rfq.rfq_source_service import RfqSourceService


class _FakeOpportunityRepository:
    def _extract_and_enrich_rfp_data(self, message_text: str):
        return {
            "title": "Opportunity from message",
            "products": [{"sku": "SKU-1"}],
            "contact": {"company_name": "ACME", "email": "buyer@acme.com", "name": "Buyer"},
        }

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None, pre_extracted_data=None):
        return {
            "status": "ok",
            "opportunity_id": opportunity_id,
            "content": content,
            "user_id": user_id,
            "pre_extracted_data": pre_extracted_data,
        }

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        return {"status": "ok", "opportunity_id": opportunity_id, "user_id": user_id}


class _FakeOpportunityRepositoryEmptyDraft(_FakeOpportunityRepository):
    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None, pre_extracted_data=None):
        return {
            "status": "ok",
            "opportunity_id": opportunity_id,
            "draft": {"products": []},
        }


class _FakeEmailRepository:
    @staticmethod
    def _clean_email_body(text: str) -> str:
        return text.strip()


class _FakeDbHandler:
    def __init__(self):
        self.account_id = "acc-1"
        self.opportunity_id = "opp-1"
        self.contact_id = "ct-1"
        self.document_ids = ["doc-rfp-1", "doc-att-1"]
        self._doc_index = 0
        self.update_calls = []

    def execute_dict_query(self, query, params=None):
        if "SELECT id FROM account WHERE name" in query:
            return []
        if "SELECT account_id FROM contact WHERE email" in query:
            return []
        if "INSERT INTO account" in query:
            return [{"id": self.account_id}]
        if "INSERT INTO opportunity" in query:
            return [{"id": self.opportunity_id}]
        if "INSERT INTO document" in query:
            document_id = self.document_ids[self._doc_index]
            self._doc_index += 1
            return [{"id": document_id}]
        if "SELECT account_id FROM opportunity" in query:
            return [{"account_id": self.account_id}]
        if "SELECT id FROM contact WHERE email" in query:
            return []
        if "INSERT INTO contact" in query:
            return [{"id": self.contact_id}]
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        self.update_calls.append((query, params))
        return 1


def test_create_rfq_source_from_html_body_creates_records_and_quote(monkeypatch, tmp_path):
    db_handler = _FakeDbHandler()
    service = RfqSourceService(
        opportunity_repository=_FakeOpportunityRepository(),
        email_repository=_FakeEmailRepository(),
        db_handler=db_handler,
    )

    monkeypatch.setattr(
        service,
        "get_form",
        lambda _body, _content_type: (
            {
                "message": "",
                "opportunity_name": "RFQ Alpha",
                "file": {
                    "filename": "rfq.pdf",
                    "content": b"%PDF-1.4",
                    "content_type": "application/pdf",
                },
            },
            None,
        ),
    )
    module = importlib.import_module(service.__class__.__module__)
    monkeypatch.setattr(module, "pick_best_rfp_source", lambda text, pdf_candidates: {"content": "pdf extracted", "extracted_data": {"products": [{"sku": "P1"}], "contact": {}}})
    monkeypatch.setattr(module, "get_storage_dir", lambda _source: tmp_path)
    monkeypatch.setattr(module.time, "time", lambda: 1700000000)

    result = service.create_rfq_source_from_html_body(
        opportunity_id="new",
        body=b"ignored",
        content_type="multipart/form-data; boundary=abc",
        user_id="u-1",
    )

    assert result["status"] == "ok"
    assert result["opportunity_id"] == "opp-1"
    assert result["document_id"] == "doc-rfp-1"
    assert result["attachment_doc_id"] == "doc-att-1"
    assert result["quote"]["status"] == "ok"
    assert any("UPDATE opportunity SET source_reference_id" in call[0] for call in db_handler.update_calls)


def test_create_rfq_source_from_html_body_requires_message_or_attachment(monkeypatch):
    service = RfqSourceService(
        opportunity_repository=_FakeOpportunityRepository(),
        email_repository=_FakeEmailRepository(),
        db_handler=_FakeDbHandler(),
    )

    monkeypatch.setattr(service, "get_form", lambda _body, _content_type: ({"message": "", "text": ""}, None))

    result = service.create_rfq_source_from_html_body(
        opportunity_id="new",
        body=b"ignored",
        content_type="multipart/form-data; boundary=abc",
        user_id="u-1",
    )

    assert result == {"status": "error", "message": "Message text or attachment is required"}


def test_create_rfq_source_from_html_body_surfaces_picker_failure(monkeypatch, tmp_path):
    db_handler = _FakeDbHandler()
    service = RfqSourceService(
        opportunity_repository=_FakeOpportunityRepository(),
        email_repository=_FakeEmailRepository(),
        db_handler=db_handler,
    )

    monkeypatch.setattr(
        service,
        "get_form",
        lambda _body, _content_type: (
            {
                "message": "Message content",
                "opportunity_name": "RFQ Alpha",
            },
            None,
        ),
    )

    module = importlib.import_module(service.__class__.__module__)
    monkeypatch.setattr(module, "extract_company_from_text", lambda _text: {})
    monkeypatch.setattr(module, "pick_best_rfp_source", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("No models loaded")))
    monkeypatch.setattr(module, "get_storage_dir", lambda _source: tmp_path)
    monkeypatch.setattr(module.time, "time", lambda: 1700000000)

    result = service.create_rfq_source_from_html_body(
        opportunity_id="new",
        body=b"ignored",
        content_type="multipart/form-data; boundary=abc",
        user_id="u-1",
    )

    assert result["status"] == "error"
    assert "RFQ extraction failed" in result["message"]
    assert "No models loaded" in result["details"]


def test_create_rfq_source_from_html_body_returns_error_when_quote_has_no_products(monkeypatch, tmp_path):
    db_handler = _FakeDbHandler()
    service = RfqSourceService(
        opportunity_repository=_FakeOpportunityRepositoryEmptyDraft(),
        email_repository=_FakeEmailRepository(),
        db_handler=db_handler,
    )

    monkeypatch.setattr(
        service,
        "get_form",
        lambda _body, _content_type: (
            {
                "message": "Message content",
                "opportunity_name": "RFQ Alpha",
            },
            None,
        ),
    )

    module = importlib.import_module(service.__class__.__module__)
    monkeypatch.setattr(module, "extract_company_from_text", lambda _text: {})
    monkeypatch.setattr(module, "pick_best_rfp_source", lambda *_args, **_kwargs: {"content": "body text", "extracted_data": {"products": []}})
    monkeypatch.setattr(module, "get_storage_dir", lambda _source: tmp_path)
    monkeypatch.setattr(module.time, "time", lambda: 1700000000)

    result = service.create_rfq_source_from_html_body(
        opportunity_id="new",
        body=b"ignored",
        content_type="multipart/form-data; boundary=abc",
        user_id="u-1",
    )

    assert result["status"] == "error"
    assert result["message"] == "RFQ extraction returned no products"
