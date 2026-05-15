"""Miscellaneous GET handlers for legacy API server."""


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
