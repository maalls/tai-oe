"""Miscellaneous GET handlers for legacy API server."""

from pathlib import Path


def handle_products_get(handler, qs):
    """Handle /api/products GET endpoint."""
    request_handlers = handler.get_request_handlers()
    return handler.json(request_handlers.handle_list_products(qs))


def handle_google_oauth_callback_get(handler, qs):
    """Handle Google OAuth callback route."""
    request_handlers = handler.get_request_handlers()
    code = qs.get('code', [None])[0]
    state = qs.get('state', [None])[0]
    if not code:
        return handler._send_error(400, 'Missing code parameter')

    result = request_handlers.handle_gmail_oauth_callback(code, state)
    if result.get('status') == 'ok':
        redirect_url = result.get('redirect_url') or 'http://localhost:5173/settings'
        return handler._send_redirect(redirect_url)

    return handler.json(result, 500)


def handle_email_fetch_loop_status_get(handler, current_file: str):
    """Handle /api/email-fetch-loop/status GET endpoint."""
    status_path = Path(current_file).resolve().parents[3] / 'var' / 'email_fetch_loop.json'
    legacy_path = Path(current_file).resolve().parents[2] / 'var' / 'email_fetch_loop.json'
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_fetch_loop_status(status_path=status_path, legacy_path=legacy_path)
    return handler.json(result)


def handle_fetch_get(handler, qs):
    """Handle /api/fetch GET endpoint."""
    target_url = qs.get('url', [None])[0]
    if not target_url:
        return handler._send_error(400, 'Missing url parameter')

    if not target_url.startswith('http://') and not target_url.startswith('https://'):
        return handler._send_error(400, 'Invalid url scheme')

    max_chars = handler._get_qs_int(qs, 'max_chars', 10000)
    timeout_ms = handler._get_qs_int(qs, 'timeout_ms', 8000)

    max_chars = max(100, min(max_chars, 50000))
    timeout_ms = max(1000, min(timeout_ms, 20000))

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_fetch_url(
            target_url=target_url,
            max_chars=max_chars,
            timeout_ms=timeout_ms,
        )
        return handler.json(result)
    except Exception as e:
        return handler._send_error(500, f'Fetch failed: {e}')
