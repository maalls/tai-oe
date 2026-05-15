from src.api.routes.server_get_mail_message_handlers import (
    handle_email_attachment_get,
    handle_gmail_classify_unclassified_get,
)


class _RequestHandlersStub:
    def handle_classify_unclassified(self, user_id=None, limit=200):
        return {"status": "ok", "user_id": user_id, "limit": limit}

    def handle_email_attachment_download(self, attachment_id, user_id):
        return 200, {"Content-Type": "text/plain"}, b"ok"


class _HandlerStub:
    def __init__(self):
        self.headers = {"Authorization": "Bearer x"}
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []
        self.errors = []
        self.response_code = None
        self.sent_headers = {}
        self.ended = False

        class _Writer:
            def __init__(self):
                self.chunks = []

            def write(self, data):
                self.chunks.append(data)

        self.wfile = _Writer()

    def get_request_handlers(self):
        return self.request_handlers

    def _get_qs_int(self, qs, key, default):
        return int(qs.get(key, [default])[0])

    def _get_optional_user_id_from_auth(self, auth_header):
        _ = auth_header
        return "u-1"

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message

    def send_response(self, code):
        self.response_code = code

    def send_header(self, key, value):
        self.sent_headers[key] = value

    def end_headers(self):
        self.ended = True


def test_handle_gmail_classify_unclassified_get_requires_user_id():
    handler = _HandlerStub()
    handler._get_optional_user_id_from_auth = lambda auth_header: None

    result = handle_gmail_classify_unclassified_get(handler, qs={})

    assert result == (400, "Missing user_id")


def test_handle_email_attachment_get_streams_binary_content():
    handler = _HandlerStub()

    result = handle_email_attachment_get(handler, "/api/email-attachment/att-1")

    assert result is None
    assert handler.response_code == 200
    assert handler.sent_headers["Content-Type"] == "text/plain"
    assert handler.wfile.chunks == [b"ok"]
