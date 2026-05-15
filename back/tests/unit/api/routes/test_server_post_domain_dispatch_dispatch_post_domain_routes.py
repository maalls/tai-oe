from types import SimpleNamespace

from src.api.routes.server_post_domain_dispatch import dispatch_post_domain_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_entity_update_post(self, match):
        self.calls.append(("entity", match.group(1), match.group(2)))

    def _handle_emails_classify_post(self, parsed_path):
        self.calls.append(("classify", parsed_path))


def test_dispatch_post_domain_routes_entity_update_regex():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/entity/opportunities/name")

    handled = dispatch_post_domain_routes(handler, parsed)

    assert handled is True
    assert handler.calls == [("entity", "opportunities", "name")]


def test_dispatch_post_domain_routes_classify_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/emails/classify/abc")

    handled = dispatch_post_domain_routes(handler, parsed)

    assert handled is True
    assert handler.calls == [("classify", "/api/emails/classify/abc")]
