#!/usr/bin/env python3
"""
Quote Management.s
Config via env:
- PORT (default 8088)
- STORAGE_DIR (default ./var/storage)
"""
import os
import sys
import http.server
import signal
import traceback
import urllib.parse
from pathlib import Path

from src.api.file.handler import FileHandler
from src.api.router import RequestHandlers
from src.api.auth.handler import AuthHandler
from src.infrastructure.runtime.env_loader import load_runtime_env
from src.infrastructure.runtime.http_server import ReusableThreadingHTTPServer
from src.infrastructure.runtime.llm_health import test_llm_connection
from src.lib.readers.csv import CSVReader
from src.api.file.handler import handle_prompt_get
from src.api.routes.dispatchers.server_delete_dispatch import dispatch_delete_request
from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_request
from src.api.routes.dispatchers.server_mutation_dispatch import dispatch_patch_request, dispatch_put_request
from src.api.routes.dispatchers.server_post_dispatch import dispatch_post_request
from src.api.routes.dispatchers.server_head_dispatch import dispatch_head_request
from src.api.routes.helpers.server_path_helpers import resolve_fs_path
from src.api.routes.helpers.server_response_helpers import send_json, send_error

# Load .env before reading config values.
load_runtime_env(__file__)
config = {
    "PORT": int(os.environ.get("PORT", "8088")),
    "STORAGE_DIR": Path(os.environ.get("STORAGE_DIR", "var/storage")).resolve(),
    "SUPABASE_URL": os.environ.get("SUPABASE_URL"),
    "DATABASE_URL": os.environ.get("DATABASE_URL"),
}


def create_rag_handler(config):
    """Factory to create HTTP request handler with config."""
    
    class Rag(http.server.SimpleHTTPRequestHandler):
        # Shared resources (class variables)
        _request_handlers = None
        _auth_handler = None

        @property
        def auth_handler(self):
            if self.__class__._auth_handler is None:
                self.__class__._auth_handler = AuthHandler()
                print("[Rag] Initialized AuthHandler")
            return self.__class__._auth_handler

        @property
        def request_handlers(self):
            if self.__class__._request_handlers is None:
                self.__class__._request_handlers = RequestHandlers(
                    FileHandler(config["STORAGE_DIR"], CSVReader())
                )
            return self.__class__._request_handlers

        def __init__(self, *args, **kwargs):
            self.config = config
            super().__init__(*args, **kwargs)

        def end_headers(self):
            # Only add wildcard CORS if we haven't already set a specific origin
            # Check if Access-Control-Allow-Origin header was already sent
            if not hasattr(self, '_cors_header_sent'):
                self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST, DELETE, PATCH')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

        def do_OPTIONS(self):
            """Handle OPTIONS method."""
            self.send_response(200)
            self.end_headers()
            return None

        def do_DELETE(self):
            """Handle DELETE method."""
            try:
                print(f"[RAG] do_DELETE called with path: {self.path}", file=sys.stderr)
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_delete_request(self, parsed.path):
                    return None

                return send_error(self, 404, "Not found")
            except Exception as e:
                traceback.print_exc()
                return send_error(self, 500, f"Server error: {str(e)}")

        def do_PATCH(self):
            """Handle PATCH method."""
            try:
                parsed = urllib.parse.urlparse(self.path)
                print(f"[RAG] PATCH request to: {parsed.path}")
                if dispatch_patch_request(self, parsed.path):
                    return None

                print(f"[RAG] PATCH path not matched: {parsed.path}")
                return send_error(self, 404, "Not found")
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] PATCH error: {e}")
                return send_error(self, 500, f"Server error: {str(e)}")

        def do_PUT(self):
            """Handle PUT method."""
            try:
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_put_request(self, parsed.path):
                    return None

                return send_error(self, 404, "Not found")
            except Exception as e:
                traceback.print_exc()
                return send_error(self, 500, f"Server error: {str(e)}")

        def do_POST(self):
            """Handle POST method."""
            try:
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_post_request(self, parsed):
                    return None

                return send_error(self, 404, "Not found")
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] Error handling request: {e}")

                return send_error(self, 500, f"Internal server error 1: {e}")

        def do_HEAD(self):
            """Handle HEAD method."""
            try:
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_head_request(self, parsed.path):
                    return None

                return send_error(self, 404, "Not found")
            except Exception as e:
                return send_error(self, 500, f"Internal server error 2: {e}")

        def do_GET(self):
            """Handle GET method."""
            try:
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)

                if dispatch_get_request(self, parsed, qs):
                    return None

                return http.server.SimpleHTTPRequestHandler.do_GET(self)
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] Error handling GET request: {e}")

                return send_error(self, 500, f"Internal server error 3: {e}")

        def _handle_prompt_get(self, parsed_path: str):
            """Handle GET requests for prompt markdown content."""
            return handle_prompt_get(self, parsed_path, __file__)

        def _resolve_fs_path(self, raw_path: str):
            return resolve_fs_path(self, current_file=__file__, raw_path=raw_path)

        def json(self, payload, status_code=200):
            """Send JSON response."""
            return send_json(self, payload, status_code=status_code)
    
    return Rag


# Backward-compatible alias used by integration tests and legacy callers.
make_handler = create_rag_handler


def main():
    if not config["STORAGE_DIR"].exists():
        print(f"Storage directory not found: {config['STORAGE_DIR']}")
        sys.exit(1)
    
    # Test LLM connection (non-blocking)
    test_llm_connection()
    
    try:
        signal.signal(signal.SIGTERM, lambda s, f: (_ for _ in ()).throw(KeyboardInterrupt()))
    except Exception:
        pass

    Handler = create_rag_handler(config)
    with ReusableThreadingHTTPServer(('', config["PORT"]), Handler) as httpd:
        print(f"CSV server on http://127.0.0.1:{config['PORT']}")
        print(f"Storage dir: {config['STORAGE_DIR']}")
        print(f"ex: http://127.0.0.1:{config['PORT']}/api/csv/sources")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            try:
                httpd.shutdown()
            except Exception:
                pass
            httpd.server_close()


if __name__ == '__main__':
    main()
