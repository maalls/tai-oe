#!/usr/bin/env python3
"""
Quote Management.s
Config via env:
- PORT (default 8088)
- STORAGE_DIR (default ./var/storage)
"""
import os
import sys
import re
import urllib.parse
import urllib.request
import http.server
import signal
import traceback
from pathlib import Path

from src.api.file.handler import FileHandler
from src.api.router import RequestHandlers
from src.api.auth.handler import AuthHandler
from src.infrastructure.runtime.env_loader import load_runtime_env
from src.infrastructure.runtime.http_server import ReusableThreadingHTTPServer
from src.infrastructure.runtime.llm_health import test_llm_connection
from src.lib.readers.csv import CSVReader
from src.api.routes.ddd_get_routes import handle_ddd_get_route, is_ddd_get_route
from src.api.routes.ddd_post_routes import handle_ddd_post_route, is_ddd_post_route
from src.api.routes.server_auth_helpers import (
    require_auth,
)
from src.api.routes.server_body_helpers import read_json
from src.api.routes.server_get_misc_handlers import (
    handle_email_fetch_loop_status_get,
    handle_prompt_get,
)
from src.api.routes.server_http_method_handlers import (
    handle_delete_method,
    handle_get_method,
    handle_head_method,
    handle_options_method,
    handle_patch_method,
    handle_post_method,
    handle_put_method,
)
from src.api.routes.server_path_helpers import resolve_fs_path
from src.api.routes.server_post_utility_handlers import (
    handle_csv_source_post,
    handle_document_extract_rfp_post,
    handle_document_update_content_post,
    handle_email_senders_verified_post,
    handle_imap_config_post,
    handle_imap_test_post,
    handle_emails_classify_post,
    handle_quote_send_post,
    handle_quote_submit_post,
    handle_rfp_post,
)
from src.api.routes.server_post_legacy_dispatch import dispatch_action_post_routes, dispatch_post_legacy_and_action_routes
from src.api.routes.server_response_helpers import send_json

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
        
        @classmethod
        def get_auth_handler(cls):
            if cls._auth_handler is None:
                cls._auth_handler = AuthHandler()
                print("[Rag] Initialized AuthHandler")
            return cls._auth_handler
        
        @classmethod
        def get_request_handlers(cls):
            if cls._request_handlers is None:
                cls._request_handlers = RequestHandlers(
                    FileHandler(config["STORAGE_DIR"], CSVReader())
                )
            return cls._request_handlers
        
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
            return handle_options_method(self)

        def do_DELETE(self):
            return handle_delete_method(self)

        def do_PATCH(self):
            return handle_patch_method(self)

        def do_PUT(self):
            return handle_put_method(self)

        def do_POST(self):
            return handle_post_method(self)

        def do_HEAD(self):
            return handle_head_method(self)

        def _handle_ddd_post_routes(self, parsed):
            """Handle incremental DDD POST routes through API adapters."""
            if not is_ddd_post_route(parsed.path):
                return False

            # Mutating DDD routes require authentication.
            if require_auth(self) is None:
                return True

            payload = read_json(self, default={})
            if not isinstance(payload, dict):
                payload = {}

            handlers = self.get_request_handlers()
            handled, response_payload, status = handle_ddd_post_route(parsed.path, payload, handlers)
            if not handled:
                return False

            self.json(response_payload, status)
            return True

        def _handle_ddd_get_routes(self, parsed, qs):
            """Handle incremental DDD GET routes through API adapters."""
            if not is_ddd_get_route(parsed.path):
                return False

            if require_auth(self) is None:
                return True

            query = {key: values[0] for key, values in qs.items() if values}
            handlers = self.get_request_handlers()
            handled, payload, status = handle_ddd_get_route(parsed.path, query, handlers)
            if not handled:
                return False
            self.json(payload, status)
            return True

        def do_GET(self):
            return handle_get_method(self)

        def _handle_email_fetch_loop_status_get(self):
            """Handle /api/email-fetch-loop/status GET endpoint."""
            return handle_email_fetch_loop_status_get(self, __file__)

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
