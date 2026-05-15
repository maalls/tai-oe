from types import SimpleNamespace

from src.api.routes.server_post_business_dispatch import dispatch_post_business_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_send_quote_for_opportunity_post(self, match):
        self.calls.append(("send_quote", match.group(1)))

    def _handle_quote_update_post(self, match):
        self.calls.append(("quote_update", match.group(1)))


def test_dispatch_post_business_routes_send_quote_regex():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunity/opp-1/send-quote")

    handled = dispatch_post_business_routes(handler, parsed)

    assert handled is True
    assert handler.calls == [("send_quote", "opp-1")]


def test_dispatch_post_business_routes_quote_update_regex():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quote/doc-8")

    handled = dispatch_post_business_routes(handler, parsed)

    assert handled is True
    assert handler.calls == [("quote_update", "doc-8")]
