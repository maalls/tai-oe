from src.api.routes.server_post_legacy_dispatch import (
    dispatch_action_post_routes,
    dispatch_post_legacy_and_action_routes,
)


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_csv_source_post(self):
        self.calls.append("csv_source")

    def _handle_action_pause_post(self, match):
        self.calls.append(("pause", match.group(1)))


def test_dispatch_post_legacy_and_action_routes_csv_source():
    handler = _HandlerStub()

    handled = dispatch_post_legacy_and_action_routes(handler, "/api/csv/source")

    assert handled is True
    assert handler.calls == ["csv_source"]


def test_dispatch_action_post_routes_pause_regex():
    handler = _HandlerStub()

    handled = dispatch_action_post_routes(handler, "/api/actions/a-1/pause")

    assert handled is True
    assert handler.calls == [("pause", "a-1")]
