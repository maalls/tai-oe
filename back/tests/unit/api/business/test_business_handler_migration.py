"""Unit tests for BusinessHandlers migration slices."""

from src.api.business.handler import BusinessHandlers


class _RfqHandlersStub:
    def __init__(self, result=None):
        self.result = result or {"status": "ok", "draft": {}}
        self.calls = []

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None):
        self.calls.append(("generate", text, message_id, user_id))
        return self.result

    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None):
        self.calls.append(("create_from_rfp", body, content_type, user_id))
        return self.result

    def handle_create_rfq_source_from_html_body(self, opportunity_id: str, body: bytes, content_type: str, user_id: str = None):
        self.calls.append(("create_rfq_source", opportunity_id, body, content_type, user_id))
        return self.result


class _EmailHandlersStub:
    def __init__(self, result=None):
        self.result = result or {"status": "ok", "opportunity": {"id": "opp-email-1"}}
        self.calls = []
        self.quote_calls = []

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None):
        self.calls.append((message_id, user_id))
        return self.result

    def handle_quote_send(self, body: bytes, content_type: str):
        self.quote_calls.append((body, content_type))
        return {"status": "ok", "message": "Quote emailed successfully"}

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: dict, user_id: str = None):
        self.quote_calls.append(("send_for_opp", opportunity_id, payload, user_id))
        return {"status": "ok", "message": "Quote email sent successfully"}


class _QuoteHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_list_quotes(self):
        self.calls.append(("list",))
        return {"status": "ok", "quotes": ["quote_1.pdf"], "total": 1}

    def handle_get_quote_file(self, filename: str):
        self.calls.append(("get", filename))
        return b"pdf-bytes"

    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None):
        self.calls.append(("generate_pdf", document_id, user_id))
        return {"status": "ok", "pdf_filename": "quote_generated.pdf"}


class _InvoiceHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None):
        self.calls.append((quote_id, user_id))
        return {
            "status": "ok",
            "invoice_id": "inv-1",
            "invoice": {
                "id": "inv-1",
                "title": "Invoice - Quote",
                "external_ref": "INV-REF",
                "currency": "EUR",
                "storage_key": "invoice_1.pdf",
                "totals": {"subtotal": 10, "tax": 2, "total": 12},
            },
        }


class _OpportunityRepositoryStub:
    def __init__(self):
        self.calls = []

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None):
        self.calls.append(("generate_with_content", opportunity_id, content, user_id))
        return {"status": "ok", "opportunity_id": opportunity_id, "content": content}

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        self.calls.append(("generate", opportunity_id, user_id))
        return {"status": "ok", "opportunity_id": opportunity_id}

    def create_opportunity_manual(self, user_id: str, name: str):
        self.calls.append(("create", user_id, name))
        return {"status": "ok", "name": name}

    def search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None):
        self.calls.append(("search", user_id, source_reference_id, name))
        return {"status": "ok", "items": []}

    def delete_opportunities(self, opportunity_ids: list[str], user_id: str = None):
        self.calls.append(("delete", opportunity_ids, user_id))
        return {"status": "ok", "deleted": opportunity_ids}


class _OpportunityHandlersStub:
    def __init__(self, repository: _OpportunityRepositoryStub):
        self.repository = repository

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None):
        return self.repository.handle_generate_quote_with_content(
            opportunity_id=opportunity_id,
            content=content,
            user_id=user_id,
        )

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        return self.repository.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)

    def handle_create_opportunity_manual(self, user_id: str, name: str):
        return self.repository.create_opportunity_manual(user_id=user_id, name=name)

    def handle_search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None):
        return self.repository.search_opportunities(
            user_id=user_id,
            source_reference_id=source_reference_id,
            name=name,
        )

    def handle_delete_opportunities(self, opportunity_ids: list[str], user_id: str = None):
        return self.repository.delete_opportunities(opportunity_ids=opportunity_ids, user_id=user_id)


class _DocumentContentServiceStub:
    def __init__(self):
        self.calls = []

    def update_document_content(self, document_id: str, content: str):
        self.calls.append((document_id, content))
        return {"status": "ok", "document_id": document_id}


class _DocumentRfpExtractionServiceStub:
    def __init__(self):
        self.calls = []

    def extract_from_document(self, document_id: str):
        self.calls.append(document_id)
        return {"status": "ok", "document_id": document_id, "data": {"products": []}}


class _DocumentHandlersStub:
    def __init__(self, content_service: _DocumentContentServiceStub, rfp_service: _DocumentRfpExtractionServiceStub):
        self.content_service = content_service
        self.rfp_service = rfp_service

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None):
        _ = user_id
        return self.content_service.update_document_content(document_id=document_id, content=content)

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None):
        _ = user_id
        return self.rfp_service.extract_from_document(document_id=document_id)

    def handle_delete_quote_document(self, document_id: str, user_id: str = None):
        _ = user_id
        return {"status": "ok", "message": "Quote deleted successfully", "document_id": document_id}

    def handle_delete_document(self, document_id: str, user_id: str = None):
        _ = user_id
        return {"status": "ok", "message": "Document deleted successfully", "document_id": document_id}

    def handle_chat_attachment_upload(self, body: bytes, content_type: str, user_id: str, opportunity_id: str):
        return {
            "status": "ok",
            "document_id": "doc-attach-1",
            "filename": "a.txt",
            "mime_type": "text/plain",
            "size": len(body),
            "storage_key": "key-a",
            "opportunity_id": opportunity_id,
            "user_id": user_id,
            "content_type": content_type,
        }

    def handle_update_line_verification(
        self,
        document_id: str,
        line_index: int,
        verification_fields: dict = None,
        is_ref_verified: bool = None,
        user_id: str = None,
    ):
        return {
            "status": "ok",
            "document_id": document_id,
            "line_index": line_index,
            "verification_fields": verification_fields,
            "is_ref_verified": is_ref_verified,
            "user_id": user_id,
        }

    def handle_get_document_file(self, filename: str):
        return f"doc-bytes::{filename}".encode("utf-8")


def _make_handler(rfq_result=None):
    handler = BusinessHandlers.__new__(BusinessHandlers)
    handler.rfq_handlers = _RfqHandlersStub(result=rfq_result)
    handler.email_handlers = _EmailHandlersStub()
    handler.quote_handlers = _QuoteHandlersStub()
    handler.invoice_handlers = _InvoiceHandlersStub()
    handler.opportunity_repository = _OpportunityRepositoryStub()
    handler.opportunity_handlers = _OpportunityHandlersStub(handler.opportunity_repository)
    handler._document_content_service = _DocumentContentServiceStub()
    handler._document_rfp_extraction_service = _DocumentRfpExtractionServiceStub()
    handler.document_handlers = _DocumentHandlersStub(
        content_service=handler._document_content_service,
        rfp_service=handler._document_rfp_extraction_service,
    )
    return handler


def test_handle_rfq_generate_delegates_to_rfq_handler():
    handler = _make_handler(rfq_result={"status": "ok", "draft": {"content": "rfq content"}})

    result = handler.handle_rfq_generate(message_id="e-1", user_id="u-1")

    assert result["status"] == "ok"
    assert result["draft"] == {"content": "rfq content"}
    assert handler.rfq_handlers.calls == [("generate", None, "e-1", "u-1")]


def test_handle_create_opportunity_from_rfp_delegates_to_rfq_handler():
    handler = _make_handler(rfq_result={"status": "ok", "opportunity": {"id": "opp-1"}})

    result = handler.handle_create_opportunity_from_rfp(body=b"payload", content_type="multipart/form-data; boundary=x", user_id="u-7")

    assert result == {"status": "ok", "opportunity": {"id": "opp-1"}}
    assert handler.rfq_handlers.calls == [
        ("create_from_rfp", b"payload", "multipart/form-data; boundary=x", "u-7")
    ]


def test_handle_create_rfq_source_from_html_body_delegates_to_rfq_handler():
    handler = _make_handler(rfq_result={"status": "ok", "opportunity": {"id": "opp-2"}})

    result = handler.handle_create_rfq_source_from_html_body(
        opportunity_id="opp-2",
        body=b"payload",
        content_type="multipart/form-data; boundary=x",
        user_id="u-8",
    )

    assert result == {"status": "ok", "opportunity": {"id": "opp-2"}}
    assert handler.rfq_handlers.calls == [
        ("create_rfq_source", "opp-2", b"payload", "multipart/form-data; boundary=x", "u-8")
    ]


def test_handle_create_opportunity_from_email_delegates_to_email_handler():
    handler = _make_handler()

    result = handler.handle_create_opportunity_from_email(message_id="email-1", user_id="u-9")

    assert result == {"status": "ok", "opportunity": {"id": "opp-email-1"}}
    assert handler.email_handlers.calls == [("email-1", "u-9")]


def test_handle_quote_send_delegates_to_email_handler():
    handler = _make_handler()

    result = handler.handle_quote_send(body=b'{"pdf_filename":"quote_a.pdf","email":"x@y.com"}', content_type="application/json")

    assert result == {"status": "ok", "message": "Quote emailed successfully"}
    assert handler.email_handlers.quote_calls == [
        (b'{"pdf_filename":"quote_a.pdf","email":"x@y.com"}', "application/json")
    ]


def test_handle_send_quote_for_opportunity_delegates_to_email_handler():
    handler = _make_handler()
    payload = {
        "to": ["client@example.com"],
        "cc": [],
        "subject": "Quote",
        "body": "Hello",
        "storage_key": "quote_a.pdf",
        "quote_id": "q-1",
    }

    result = handler.handle_send_quote_for_opportunity("opp-99", payload, user_id="u-2")

    assert result == {"status": "ok", "message": "Quote email sent successfully"}
    assert handler.email_handlers.quote_calls[-1] == ("send_for_opp", "opp-99", payload, "u-2")


def test_handle_list_quotes_delegates_to_quote_handler():
    handler = _make_handler()

    result = handler.handle_list_quotes()

    assert result == {"status": "ok", "quotes": ["quote_1.pdf"], "total": 1}
    assert handler.quote_handlers.calls == [("list",)]


def test_handle_get_quote_file_delegates_to_quote_handler():
    handler = _make_handler()

    result = handler.handle_get_quote_file("quote_1.pdf")

    assert result == b"pdf-bytes"
    assert handler.quote_handlers.calls == [("get", "quote_1.pdf")]


def test_handle_generate_quote_pdf_delegates_to_quote_handler():
    handler = _make_handler()

    result = handler.handle_generate_quote_pdf("doc-q-1", user_id="u-1")

    assert result == {"status": "ok", "pdf_filename": "quote_generated.pdf"}
    assert handler.quote_handlers.calls == [("generate_pdf", "doc-q-1", "u-1")]


def test_handle_generate_invoice_from_quote_delegates_to_invoice_handler():
    handler = _make_handler()

    result = handler.handle_generate_invoice_from_quote("quote-1", user_id="u-1")

    assert result["status"] == "ok"
    assert result["invoice_id"] == "inv-1"
    assert handler.invoice_handlers.calls == [("quote-1", "u-1")]


def test_business_handler_opportunity_wrappers_are_class_methods():
    handler = _make_handler()

    create_result = handler.handle_create_opportunity_manual("u-1", "Deal")
    search_result = handler.handle_search_opportunities("u-1", source_reference_id="src-1", name="Deal")
    delete_result = handler.handle_delete_opportunities(["opp-1"], user_id="u-1")
    generate_result = handler.handle_generate_quote_for_opportunity("opp-1", user_id="u-1")

    assert create_result == {"status": "ok", "name": "Deal"}
    assert search_result == {"status": "ok", "items": []}
    assert delete_result == {"status": "ok", "deleted": ["opp-1"]}
    assert generate_result == {"status": "ok", "opportunity_id": "opp-1"}


def test_handle_update_document_content_delegates_to_document_content_service():
    handler = _make_handler()

    result = handler.handle_update_document_content("doc-1", "new content", user_id="u-1")

    assert result == {"status": "ok", "document_id": "doc-1"}
    assert handler._document_content_service.calls == [("doc-1", "new content")]


def test_handle_extract_rfp_from_document_delegates_to_document_rfp_service():
    handler = _make_handler()

    result = handler.handle_extract_rfp_from_document("doc-77", user_id="u-1")

    assert result == {"status": "ok", "document_id": "doc-77", "data": {"products": []}}
    assert handler._document_rfp_extraction_service.calls == ["doc-77"]


def test_handle_delete_quote_document_delegates_to_document_handler():
    handler = _make_handler()

    result = handler.handle_delete_quote_document("doc-q-1", user_id="u-1")

    assert result == {"status": "ok", "message": "Quote deleted successfully", "document_id": "doc-q-1"}


def test_handle_delete_document_delegates_to_document_handler():
    handler = _make_handler()

    result = handler.handle_delete_document("doc-1", user_id="u-1")

    assert result == {"status": "ok", "message": "Document deleted successfully", "document_id": "doc-1"}


def test_handle_chat_attachment_upload_delegates_to_document_handler():
    handler = _make_handler()

    result = handler.handle_chat_attachment_upload(
        body=b"payload",
        content_type="multipart/form-data; boundary=x",
        user_id="u-1",
        opportunity_id="opp-1",
    )

    assert result["status"] == "ok"
    assert result["document_id"] == "doc-attach-1"
    assert result["opportunity_id"] == "opp-1"
    assert result["user_id"] == "u-1"


def test_handle_update_line_verification_delegates_to_document_handler():
    handler = _make_handler()

    result = handler.handle_update_line_verification(
        document_id="doc-1",
        line_index=2,
        verification_fields={"is_ref_verified": True},
        user_id="u-1",
    )

    assert result["status"] == "ok"
    assert result["document_id"] == "doc-1"
    assert result["line_index"] == 2
    assert result["verification_fields"] == {"is_ref_verified": True}
    assert result["user_id"] == "u-1"


def test_handle_get_document_file_delegates_to_document_handler():
    handler = _make_handler()

    result = handler.handle_get_document_file("doc.pdf")

    assert result == b"doc-bytes::doc.pdf"