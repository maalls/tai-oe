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


class _OpportunityRepositoryStub:
    def __init__(self):
        self.calls = []

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


def _make_handler(rfq_result=None):
    handler = BusinessHandlers.__new__(BusinessHandlers)
    handler.rfq_handlers = _RfqHandlersStub(result=rfq_result)
    handler.email_handlers = _EmailHandlersStub()
    handler.opportunity_repository = _OpportunityRepositoryStub()
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