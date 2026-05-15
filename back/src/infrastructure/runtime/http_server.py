"""HTTP server runtime helpers."""

import http.server
import socket


class ReusableThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True

    def server_bind(self):
        """Ensure SO_REUSEADDR before binding to support quick restarts."""
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()
