from src.api.routes.server_post_utility_handlers import handle_chat_attachments_post


class _ParsedStub:
    query = "opportunity_id=opp-1"


class _RequestHandlersStub:
    def handle_chat_attachment_upload(self, body, content_type, user_id, opportunity_id):
        return {
            "status": "ok",
            "body": body,
            "content_type": content_type,
            "user_id": user_id,
            "opportunity_id": opportunity_id,
        }


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.headers = {"Content-Type": "application/octet-stream"}

    def _read_body(self):
        return b"abc"

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200

    def json(self, payload, status=200):
        return payload, status


def test_handle_chat_attachments_post_reads_query_and_uploads():
    handler = _HandlerStub()

    result = handle_chat_attachments_post(handler, _ParsedStub())

    assert result == (
        {
            "status": "ok",
            "body": b"abc",
            "content_type": "application/octet-stream",
            "user_id": "u-1",
            "opportunity_id": "opp-1",
        },
        200,
    )
