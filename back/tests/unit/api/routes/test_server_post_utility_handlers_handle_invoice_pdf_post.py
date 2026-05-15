from src.api.routes.server_post_utility_handlers import handle_invoice_pdf_post


class _MatchStub:
    def group(self, idx):
        assert idx == 1
        return "inv-1"


class _RequestHandlersStub:
    def handle_generate_invoice_pdf(self, document_id, user_id):
        return {"status": "ok", "document_id": document_id, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200

    def json(self, payload, status=200):
        return payload, status


def test_handle_invoice_pdf_post_forwards_ids():
    handler = _HandlerStub()

    result = handle_invoice_pdf_post(handler, _MatchStub())

    assert result == ({"status": "ok", "document_id": "inv-1", "user_id": "u-1"}, 200)
