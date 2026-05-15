from src.api.routes.server_http_method_handlers import handle_options_method


class _HandlerStub:
    def __init__(self):
        self.response_codes = []
        self.ended = False

    def send_response(self, code):
        self.response_codes.append(code)

    def end_headers(self):
        self.ended = True


def test_handle_options_method_sends_200_and_ends_headers():
    handler = _HandlerStub()

    result = handle_options_method(handler)

    assert result is None
    assert handler.response_codes == [200]
    assert handler.ended is True
