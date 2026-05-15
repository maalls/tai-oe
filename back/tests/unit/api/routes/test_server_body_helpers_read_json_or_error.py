from io import BytesIO

from src.api.routes.server_body_helpers import read_json_or_error


class _HandlerStub:
    def __init__(self, body):
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = BytesIO(body)
        self.json_calls = []

    def json(self, payload, status_code=200):
        self.json_calls.append((payload, status_code))
        return payload, status_code


def test_read_json_or_error_returns_decoded_payload():
    handler = _HandlerStub(b'{"ok": true}')

    result = read_json_or_error(handler)

    assert result == {"ok": True}


def test_read_json_or_error_emits_error_payload_on_invalid_json():
    handler = _HandlerStub(b"not-json")

    result = read_json_or_error(handler, status_code=422)

    assert result is None
    assert handler.json_calls == [({"status": "error", "message": "Invalid JSON"}, 422)]
