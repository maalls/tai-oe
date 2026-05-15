from src.api.routes.server_post_utility_handlers import handle_document_extract_rfp_post


class _RequestHandlersStub:
    def handle_extract_rfp_from_document(self, document_id, user_id):
        return {"status": "ok", "document_id": document_id, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.headers = {"Authorization": "Bearer token"}

    def _read_json(self, default=None):
        return {"document_id": "doc-1"}

    def _require_auth(self, auth_header=None):
        assert auth_header == "Bearer token"
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_document_extract_rfp_post_passes_document_id_and_user_id():
    handler = _HandlerStub()

    result = handle_document_extract_rfp_post(handler)

    assert result == ({"status": "ok", "document_id": "doc-1", "user_id": "u-1"}, 200)
