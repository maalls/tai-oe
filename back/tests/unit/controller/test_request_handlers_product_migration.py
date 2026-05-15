"""Unit tests for RequestHandlers product delegation during migration."""

from src.controller.handlers import RequestHandlers


class _ProductControllerStub:
    def __init__(self):
        self.calls = []

    def list(self, qs):
        self.calls.append(("list", qs))
        return [{"id": "p-1"}]

    def post(self, payload):
        self.calls.append(("post", payload))
        return {"id": "p-2", "name": payload.get("name")}


def test_handle_list_products_uses_product_controller(monkeypatch):
    stub = _ProductControllerStub()
    monkeypatch.setattr("src.controller.handlers.ProductController", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_list_products({"q": ["x"]})

    assert result == {"products": [{"id": "p-1"}]}
    assert stub.calls == [("list", {"q": ["x"]})]


def test_handle_create_product_uses_product_controller(monkeypatch):
    stub = _ProductControllerStub()
    monkeypatch.setattr("src.controller.handlers.ProductController", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_create_product({"name": "Widget"})

    assert result == {"status": "ok", "product": {"id": "p-2", "name": "Widget"}}
    assert stub.calls == [("post", {"name": "Widget"})]
