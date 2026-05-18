from types import SimpleNamespace

from src.api.routes.dispatchers import server_get_dispatch


class _HandlerStub:
    pass


def test_dispatch_get_request_short_circuits_on_misc(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/anything")

    monkeypatch.setattr(server_get_dispatch, "dispatch_get_misc_routes", lambda h, p, q: True)

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is True


def test_dispatch_get_request_uses_mail_group(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/gmail/status")

    monkeypatch.setattr(server_get_dispatch, "dispatch_get_misc_routes", lambda h, p, q: False)
    monkeypatch.setattr(server_get_dispatch, "dispatch_get_mail_routes", lambda h, p, q: True)

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is True
