"""HTTP method handlers for legacy API server."""

import sys
import traceback
import urllib.parse

from src.api.routes.server_delete_dispatch import dispatch_delete_request
from src.api.routes.server_mutation_dispatch import dispatch_patch_request
from src.api.routes.server_head_dispatch import dispatch_head_request


def handle_options_method(handler):
    """Handle OPTIONS method."""
    handler.send_response(200)
    handler.end_headers()
    return None


def handle_head_method(handler):
    """Handle HEAD method."""
    try:
        parsed = urllib.parse.urlparse(handler.path)

        if dispatch_head_request(handler, parsed.path):
            return None

        return handler._send_error(404, "Not found")
    except Exception as e:
        return handler._send_error(500, f"Internal server error 2: {e}")


def handle_delete_method(handler):
    """Handle DELETE method."""
    try:
        print(f"[RAG] do_DELETE called with path: {handler.path}", file=sys.stderr)
        parsed = urllib.parse.urlparse(handler.path)

        if dispatch_delete_request(handler, parsed.path):
            return None

        return handler._send_error(404, "Not found")
    except Exception as e:
        traceback.print_exc()
        return handler._send_error(500, f"Server error: {str(e)}")


def handle_patch_method(handler):
    """Handle PATCH method."""
    try:
        parsed = urllib.parse.urlparse(handler.path)
        print(f"[RAG] PATCH request to: {parsed.path}")
        if dispatch_patch_request(handler, parsed.path):
            return None

        print(f"[RAG] PATCH path not matched: {parsed.path}")
        return handler._send_error(404, "Not found")
    except Exception as e:
        traceback.print_exc()
        print(f"[RAG] PATCH error: {e}")
        return handler._send_error(500, f"Server error: {str(e)}")
