from src.api.routes.server_body_helpers import read_json


class _HandlerStub:
    def __init__(self, body):
        self.body = body

    def _read_body(self):
        return self.body


def test_read_json_returns_decoded_payload():
    handler = _HandlerStub(b'{"x": 1}')

    result = read_json(handler)

    assert result == {"x": 1}


def test_read_json_returns_default_on_invalid_json():
    handler = _HandlerStub(b"not-json")

    result = read_json(handler, default={"fallback": True})

    assert result == {"fallback": True}
