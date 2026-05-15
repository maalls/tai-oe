from src.api.routes.server_get_misc_handlers import handle_products_get


class _RequestHandlersStub:
    def handle_list_products(self, qs):
        return {"status": "ok", "qs": qs}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_products_get_returns_products_payload():
    handler = _HandlerStub()

    result = handle_products_get(handler, {"limit": ["10"]})

    assert result == ({"status": "ok", "qs": {"limit": ["10"]}}, 200)
