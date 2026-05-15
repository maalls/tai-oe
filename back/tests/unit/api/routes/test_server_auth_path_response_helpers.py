from pathlib import Path

from src.api.routes.server_auth_helpers import get_optional_user_id_from_auth, require_auth_user_id
from src.api.routes.server_path_helpers import resolve_fs_path
from src.api.routes.server_response_helpers import send_redirect


class _AuthHandlerStub:
    def __init__(self, user_data):
        self.user_data = user_data
        self.calls = []

    def _require_auth(self, auth_header=None, required=True):
        self.calls.append((auth_header, required))
        return self.user_data


class _PathHandlerStub:
    def __init__(self):
        self.errors = []

    def _send_error(self, code, message):
        self.errors.append((code, message))


class _RedirectHandlerStub:
    def __init__(self):
        self.calls = []

    def send_response(self, code):
        self.calls.append(("code", code))

    def send_header(self, key, value):
        self.calls.append((key, value))

    def end_headers(self):
        self.calls.append(("end", None))


def test_get_optional_user_id_from_auth_uses_non_required_auth():
    handler = _AuthHandlerStub(user_data={"id": "u-1"})

    user_id = get_optional_user_id_from_auth(handler, "Bearer token")

    assert user_id == "u-1"
    assert handler.calls == [("Bearer token", False)]


def test_require_auth_user_id_returns_none_when_auth_fails():
    handler = _AuthHandlerStub(user_data=None)

    user_id = require_auth_user_id(handler)

    assert user_id is None
    assert handler.calls == [(None, True)]


def test_resolve_fs_path_rejects_outside_base_dir():
    handler = _PathHandlerStub()

    resolved = resolve_fs_path(handler, current_file=__file__, raw_path="../../../../etc/passwd")

    assert resolved is None
    assert handler.errors == [(400, "Invalid path")]


def test_resolve_fs_path_accepts_relative_project_path():
    handler = _PathHandlerStub()

    resolved = resolve_fs_path(handler, current_file=__file__, raw_path="back/src")

    assert isinstance(resolved, Path)
    assert resolved.name == "src"


def test_send_redirect_writes_location_header():
    handler = _RedirectHandlerStub()

    send_redirect(handler, "http://localhost:5173", code=302)

    assert handler.calls == [
        ("code", 302),
        ("Location", "http://localhost:5173"),
        ("end", None),
    ]
