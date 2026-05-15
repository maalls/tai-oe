from src.api.routes.server_post_utility_handlers import handle_auth_signup_post


class _RequestHandlersStub:
    def handle_auth_signup(self, body):
        _ = body
        return {"status": "ok", "status_code": 201}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_body(self):
        return b'{"email":"x@example.org"}'

    def get_request_handlers(self):
        return self.request_handlers

    def _pop_status(self, payload):
        return payload.pop("status_code", 200)

    def json(self, payload, status=200):
        return payload, status


def test_handle_auth_signup_post_uses_body_and_status_from_payload():
    handler = _HandlerStub()

    result = handle_auth_signup_post(handler)

    assert result == ({"status": "ok"}, 201)
