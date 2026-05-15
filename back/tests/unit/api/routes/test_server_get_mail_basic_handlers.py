from src.api.routes.server_get_mail_basic_handlers import (
    handle_gmail_status_get,
    handle_imap_status_get,
)


class _RequestHandlersStub:
    def handle_gmail_status(self, user_id=None):
        return {"user_id": user_id}

    def handle_imap_status(self, user_id=None):
        return {"imap": user_id}


class _HandlerStub:
    def __init__(self, user_id="u-1"):
        self._user_id = user_id
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def _get_qs_value(self, qs, key, default=None):
        return qs.get(key, [default])[0]

    def _require_auth_user_id(self):
        return self._user_id

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_gmail_status_get_uses_user_id_query_param():
    handler = _HandlerStub()

    result = handle_gmail_status_get(handler, {"user_id": ["u-42"]})

    assert result == ({"user_id": "u-42"}, 200)


def test_handle_imap_status_get_returns_none_when_unauthenticated():
    handler = _HandlerStub(user_id=None)

    result = handle_imap_status_get(handler)

    assert result is None
    assert handler.json_calls == []
