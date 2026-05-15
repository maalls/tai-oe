from src.api.routes.server_get_misc_handlers import handle_google_oauth_callback_get


class _RequestHandlersStub:
    def __init__(self, result):
        self.result = result

    def handle_gmail_oauth_callback(self, code, state):
        return {**self.result, "code": code, "state": state}


class _HandlerStub:
    def __init__(self, request_handlers):
        self.request_handlers = request_handlers
        self.errors = []
        self.redirects = []
        self.json_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message

    def _send_redirect(self, location, code=302):
        self.redirects.append((location, code))
        return location, code

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_google_oauth_callback_get_requires_code():
    handler = _HandlerStub(_RequestHandlersStub({"status": "ok"}))

    result = handle_google_oauth_callback_get(handler, {"state": ["s"]})

    assert result == (400, "Missing code parameter")


def test_handle_google_oauth_callback_get_redirects_on_success():
    handler = _HandlerStub(_RequestHandlersStub({"status": "ok"}))

    result = handle_google_oauth_callback_get(handler, {"code": ["c1"], "state": ["s1"]})

    assert result == ("http://localhost:5173/settings", 302)
