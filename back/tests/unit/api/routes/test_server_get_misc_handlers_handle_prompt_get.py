from src.api.routes.server_get_misc_handlers import handle_prompt_get


class _RequestHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_get_prompt_content(self, relative_path, prompt_base_dir):
        self.calls.append((relative_path, prompt_base_dir))
        return "# prompt"


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.errors = []
        self.text_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message

    def _send_text_response(self, code, content_type, body=None):
        self.text_calls.append((code, content_type, body))
        return code, content_type, body


def test_handle_prompt_get_returns_text_response():
    handler = _HandlerStub()

    result = handle_prompt_get(
        handler,
        "/api/prompt/sales/system.md",
        "/Users/malo/Documents/Projects/tai-oe/back/src/api/server.py",
    )

    assert result == (200, "text/plain; charset=utf-8", b"# prompt")
    relative_path, _prompt_base_dir = handler.request_handlers.calls[0]
    assert relative_path == "sales/system.md"


def test_handle_prompt_get_maps_value_error_to_400():
    class _FailingRequestHandlersStub:
        def handle_get_prompt_content(self, relative_path, prompt_base_dir):
            _ = relative_path
            _ = prompt_base_dir
            raise ValueError("bad path")

    handler = _HandlerStub()
    handler.request_handlers = _FailingRequestHandlersStub()

    result = handle_prompt_get(
        handler,
        "/api/prompt/../../secret.md",
        "/Users/malo/Documents/Projects/tai-oe/back/src/api/server.py",
    )

    assert result == (400, "bad path")
