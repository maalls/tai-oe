"""Miscellaneous GET route dispatch for legacy API server."""

from src.api.email.handler import handle_google_oauth_callback_get
from src.api.file.handler import handle_fetch_get, handle_storage_get
from src.api.product.handler import handle_products_get


def dispatch_get_misc_routes(handler, parsed, qs) -> bool:
    """Dispatch misc GET routes and return True when handled."""
    if parsed.path == '/api/products':
        handle_products_get(handler, qs)
        return True

    if parsed.path.startswith('/api/google/oauth/callback'):
        handle_google_oauth_callback_get(handler, qs)
        return True

    if parsed.path.startswith('/api/prompt/'):
        handler._handle_prompt_get(parsed.path)
        return True

    if parsed.path == '/api/fetch':
        handle_fetch_get(handler, qs)
        return True

    if parsed.path == '/api/email-fetch-loop/status':
        handler._handle_email_fetch_loop_status_get()
        return True

    if parsed.path.startswith('/api/storage/'):
        handle_storage_get(handler, handler.config['STORAGE_DIR'], parsed.path)
        return True

    return False
