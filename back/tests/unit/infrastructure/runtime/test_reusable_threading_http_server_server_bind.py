import http.server

from src.infrastructure.runtime.http_server import ReusableThreadingHTTPServer


class _NoopHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        _ = (format, args)


def test_reusable_threading_http_server_server_bind_allocates_ephemeral_port():
    server = ReusableThreadingHTTPServer(("127.0.0.1", 0), _NoopHandler)
    try:
        assert server.server_address[1] > 0
        assert server.allow_reuse_address is True
    finally:
        server.server_close()
