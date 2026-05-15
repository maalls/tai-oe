from src.api.routes.server_post_utility_handlers import handle_document_update_content_post


class _RequestHandlersStub:
    def handle_update_document_content(self, document_id, content, user_id):
        return {"status": "ok", "document_id": document_id, "content": content, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        return {"document_id": "doc-1", "content": "hello"}

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_document_update_content_post_forwards_payload_and_user_id():
    handler = _HandlerStub()

    result = handle_document_update_content_post(handler)

    assert result == (
        {"status": "ok", "document_id": "doc-1", "content": "hello", "user_id": "u-1"},
        200,
    )
