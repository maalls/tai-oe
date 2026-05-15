"""Miscellaneous GET route dispatch for legacy API server."""

from src.api.email.handler import handle_google_oauth_callback_get
from src.api.file.routes import dispatch_file_routes
from src.api.product.routes import dispatch_product_routes


def dispatch_get_misc_routes(handler, parsed, qs) -> bool:
    """Dispatch misc GET routes and return True when handled."""
    request_handlers = handler.request_handlers

    if dispatch_product_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    if parsed.path.startswith('/api/google/oauth/callback'):
        handle_google_oauth_callback_get(handler, qs)
        return True

    if parsed.path.startswith('/api/prompt/'):
        handler._handle_prompt_get(parsed.path)
        return True

    if parsed.path == '/api/email-fetch-loop/status':
        handler._handle_email_fetch_loop_status_get()
        return True

    if dispatch_file_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    return False
