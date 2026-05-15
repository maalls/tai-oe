"""Unit tests for RequestHandlers opportunity delegation during migration."""

from src.controller.handlers import RequestHandlers


class _BusinessHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        self.calls.append(("generate", opportunity_id, user_id))
        return {"status": "ok", "opportunity_id": opportunity_id}

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None):
        self.calls.append(("create_from_email", message_id, user_id))
        return {"status": "ok", "opportunity": {"id": "opp-1"}}

    def handle_create_opportunity_manual(self, user_id: str, name: str):
        self.calls.append(("create_manual", user_id, name))
        return {"status": "ok", "name": name}

    def handle_search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None):
        self.calls.append(("search", user_id, source_reference_id, name))
        return {"status": "ok", "items": []}

    def handle_delete_opportunities(self, opportunity_ids: list[str], user_id: str = None):
        self.calls.append(("delete", opportunity_ids, user_id))
        return {"status": "ok", "deleted": opportunity_ids}

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: dict, user_id: str = None):
        self.calls.append(("send_quote", opportunity_id, payload, user_id))
        return {"status": "ok", "message": "Quote email sent successfully"}

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None):
        self.calls.append(("update_document_content", document_id, content, user_id))
        return {"status": "ok", "document_id": document_id}

    def handle_quote_submit(self, body: bytes, content_type: str):
        self.calls.append(("quote_submit", body, content_type))
        return {"status": "ok", "quote": {"id": "q-1"}}


class _EmailHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_email_resync(self, email_id: str, provider_message_id: str, user_id: str):
        self.calls.append((email_id, provider_message_id, user_id))
        return {"status": "ok", "email_id": email_id}


def _make_request_handlers_with_stub(stub: _BusinessHandlersStub) -> RequestHandlers:
    handlers = RequestHandlers.__new__(RequestHandlers)
    handlers.business_handlers = stub
    return handlers


def _make_request_handlers_with_email_stub(stub: _EmailHandlersStub) -> RequestHandlers:
    handlers = RequestHandlers.__new__(RequestHandlers)
    handlers.email_handlers = stub
    return handlers


def test_handle_generate_quote_for_opportunity_uses_business_handler_method():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_generate_quote_for_opportunity("opp-42", user_id="u-1")

    assert result == {"status": "ok", "opportunity_id": "opp-42"}
    assert stub.calls == [("generate", "opp-42", "u-1")]


def test_handle_create_opportunity_from_email_triggers_quote_generation_via_business_handler():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_create_opportunity_from_email("email-1", user_id="u-2")

    assert result["status"] == "ok"
    assert stub.calls == [
        ("create_from_email", "email-1", "u-2"),
        ("generate", "opp-1", "u-2"),
    ]


def test_handle_create_opportunity_manual_uses_business_handler_method():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_create_opportunity_manual(user_id="u-3", name="Deal")

    assert result == {"status": "ok", "name": "Deal"}
    assert stub.calls == [("create_manual", "u-3", "Deal")]


def test_handle_search_opportunities_uses_business_handler_method():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_search_opportunities(
        user_id="u-4",
        source_reference_id="src-1",
        name="Alpha",
    )

    assert result == {"status": "ok", "items": []}
    assert stub.calls == [("search", "u-4", "src-1", "Alpha")]


def test_handle_delete_opportunity_splits_csv_ids_before_delegating():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_delete_opportunity("opp-1, opp-2 ,,opp-3", user_id="u-5")

    assert result == {"status": "ok", "deleted": ["opp-1", "opp-2", "opp-3"]}
    assert stub.calls == [("delete", ["opp-1", "opp-2", "opp-3"], "u-5")]


def test_handle_email_resync_uses_email_handler_method():
    stub = _EmailHandlersStub()
    handlers = _make_request_handlers_with_email_stub(stub)

    result = handlers.handle_email_resync("e-1", "gmail-1", "u-6")

    assert result == {"status": "ok", "email_id": "e-1"}
    assert stub.calls == [("e-1", "gmail-1", "u-6")]


def test_handle_send_quote_for_opportunity_uses_business_handler_method():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)
    payload = {"to": ["a@example.com"], "subject": "s", "body": "b", "quote_id": "q-1"}

    result = handlers.handle_send_quote_for_opportunity("opp-7", payload=payload, user_id="u-8")

    assert result == {"status": "ok", "message": "Quote email sent successfully"}
    assert stub.calls == [("send_quote", "opp-7", payload, "u-8")]


def test_handle_update_document_content_uses_business_handler_method():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_update_document_content("doc-1", "new content", user_id="u-9")

    assert result == {"status": "ok", "document_id": "doc-1"}
    assert stub.calls == [("update_document_content", "doc-1", "new content", "u-9")]


def test_handle_quote_submit_uses_business_handler_method():
    stub = _BusinessHandlersStub()
    handlers = _make_request_handlers_with_stub(stub)

    result = handlers.handle_quote_submit(b"{}", "application/json")

    assert result == {"status": "ok", "quote": {"id": "q-1"}}
    assert stub.calls == [("quote_submit", b"{}", "application/json")]


class _QuoteControllerStub:
    def __init__(self):
        self.calls = []

    def update(self, document_id: str, payload: dict, user_id: str = None):
        self.calls.append((document_id, payload, user_id))
        return {"status": "ok", "updated": document_id}


def test_handle_update_quote_uses_quote_controller(monkeypatch):
    controller_stub = _QuoteControllerStub()
    monkeypatch.setattr("src.controller.handlers.QuoteController", lambda: controller_stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_update_quote("doc-9", {"content": "v2"}, user_id="u-10")

    assert result == {"status": "ok", "updated": "doc-9"}
    assert controller_stub.calls == [("doc-9", {"content": "v2"}, "u-10")]