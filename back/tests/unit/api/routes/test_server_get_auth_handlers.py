from src.api.routes.server_get_auth_handlers import (
    handle_auth_user_get,
    handle_oauth_callback_get,
    handle_oauth_login_get,
)


class _RequestHandlersStub:
    def handle_auth_user(self, auth_header):
        return {"status": 200, "auth": auth_header}

    def handle_oauth_login(self, provider, redirect_url=None):
        return {"status": "ok", "provider": provider, "redirect_url": redirect_url}

    def handle_oauth_callback(self, provider, code, state=None):
        return {
            "status": "ok",
            "provider": provider,
            "code": code,
            "state": state,
            "redirect_url": "http://localhost:5173/settings",
        }


class _HandlerStub:
    def __init__(self):
        self.headers = {"Authorization": "Bearer x"}
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []
        self.redirect_calls = []
        self.error_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def _get_qs_value(self, qs, key, default=None):
        return qs.get(key, [default])[0]

    def _pop_status(self, result):
        return result.pop("status", 200)

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status

    def _send_redirect(self, location):
        self.redirect_calls.append(location)
        return location

    def _send_error(self, code, message):
        self.error_calls.append((code, message))
        return code, message


def test_handle_auth_user_get_uses_auth_header_and_pop_status():
    handler = _HandlerStub()

    result = handle_auth_user_get(handler)

    assert result == ({"auth": "Bearer x"}, 200)


def test_handle_oauth_login_get_validates_provider():
    handler = _HandlerStub()

    result = handle_oauth_login_get(handler, qs={})

    assert result == (400, "Missing provider parameter")


def test_handle_oauth_callback_get_redirects_on_success():
    handler = _HandlerStub()

    result = handle_oauth_callback_get(handler, qs={"provider": ["azure"], "code": ["c1"]})

    assert result == "http://localhost:5173/settings"
    assert handler.redirect_calls == ["http://localhost:5173/settings"]
    assert handler.json_calls == []
