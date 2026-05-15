from src.api.routes.server_post_utility_handlers import handle_fs_read_post


class _PathStub:
    def __init__(self, exists=True, is_file=True):
        self._exists = exists
        self._is_file = is_file

    def exists(self):
        return self._exists

    def is_file(self):
        return self._is_file


class _RequestHandlersStub:
    def handle_fs_read(self, target_path, max_chars):
        return {"status": "ok", "max_chars": max_chars, "path": target_path}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        _ = default
        return {"path": "docs/readme.md", "max_chars": 120000}

    def _get_payload_int(self, payload, key, default):
        return int(payload.get(key, default))

    def _resolve_fs_path(self, raw_path):
        _ = raw_path
        return _PathStub(exists=True, is_file=True)

    def get_request_handlers(self):
        return self.request_handlers

    def _send_error(self, code, message):
        return code, message

    def json(self, payload, status=200):
        return payload, status


def test_handle_fs_read_post_clamps_max_chars_and_reads_file():
    handler = _HandlerStub()

    result = handle_fs_read_post(handler)

    payload, status = result
    assert status == 200
    assert payload["status"] == "ok"
    assert payload["max_chars"] == 50000
