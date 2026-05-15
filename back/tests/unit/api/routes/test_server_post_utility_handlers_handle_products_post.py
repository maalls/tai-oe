from src.api.routes.server_post_utility_handlers import handle_products_post


class _RequestHandlersStub:
    def handle_create_product(self, payload):
        return {"status": "ok", "payload": payload}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        _ = default
        return {"name": "p1"}

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        return payload, status


def test_handle_products_post_returns_201_with_created_payload():
    handler = _HandlerStub()

    result = handle_products_post(handler)

    assert result == ({"status": "ok", "payload": {"name": "p1"}}, 201)
