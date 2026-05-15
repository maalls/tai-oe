"""Miscellaneous GET route dispatch for legacy API server."""


def dispatch_get_misc_routes(handler, parsed, qs) -> bool:
    """Dispatch misc GET routes and return True when handled."""
    if parsed.path == '/api/products':
        handler._handle_products_get(qs)
        return True

    if parsed.path.startswith('/api/google/oauth/callback'):
        handler._handle_google_oauth_callback_get(qs)
        return True

    if parsed.path.startswith('/api/prompt/'):
        handler._handle_prompt_get(parsed.path)
        return True

    if parsed.path == '/api/fetch':
        handler._handle_fetch_get(qs)
        return True

    if parsed.path == '/api/email-fetch-loop/status':
        handler._handle_email_fetch_loop_status_get()
        return True

    if parsed.path.startswith('/api/storage/'):
        handler._handle_storage_get(parsed.path)
        return True

    return False
