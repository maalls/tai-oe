from src.api.routes.server_post_utility_handlers import handle_fs_create_post


class _RequestHandlersStub:
    def handle_fs_create(self, target_path, kind):
        return {"status": "ok", "target_path": str(target_path), "kind": kind}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        _ = default
        return {"path": "docs/new", "type": "dir"}

    def _resolve_fs_path(self, raw_path):
        return f"/resolved/{raw_path}"

    def get_request_handlers(self):
        return self.request_handlers

    def _send_error(self, code, message):
        return code, message

    def json(self, payload, status=200):
        return payload, status


def test_handle_fs_create_post_delegates_to_service():
    handler = _HandlerStub()

    result = handle_fs_create_post(handler)

    assert result == ({"status": "ok", "target_path": "/resolved/docs/new", "kind": "dir"}, 200)
