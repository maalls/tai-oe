from src.api.routes.server_post_utility_handlers import handle_auth_logout_post


class _RequestHandlersStub:
    def handle_auth_logout(self, auth_header):
        return {"status": "ok", "auth_header": auth_header, "status_code": 200}


class _HandlerStub:
    def __init__(self):
        self.headers = {"Authorization": "Bearer abc"}
        self.request_handlers = _RequestHandlersStub()

    def get_request_handlers(self):
        return self.request_handlers

    def _pop_status(self, payload):
        return payload.pop("status_code", 200)

    def json(self, payload, status=200):
        return payload, status


def test_handle_auth_logout_post_uses_auth_header_and_status():
    handler = _HandlerStub()

    result = handle_auth_logout_post(handler)

    assert result == ({"status": "ok", "auth_header": "Bearer abc"}, 200)
