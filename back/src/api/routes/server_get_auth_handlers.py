"""Auth/OAuth GET handlers for legacy API server."""


def handle_auth_user_get(handler):
    """Handle /api/auth/user GET endpoint."""
    auth_header = handler.headers.get('Authorization', '')
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_user(auth_header)
    status = handler._pop_status(result)
    return handler.json(result, status)


def handle_oauth_login_get(handler, qs):
    """Handle /api/oauth/login GET endpoint."""
    provider = handler._get_qs_value(qs, 'provider')
    if not provider:
        return handler._send_error(400, 'Missing provider parameter')
    redirect_url = handler._get_qs_value(qs, 'redirect_url')

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_oauth_login(provider=provider, redirect_url=redirect_url)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_oauth_callback_get(handler, qs):
    """Handle /api/oauth/callback GET endpoint."""
    provider = handler._get_qs_value(qs, 'provider')
    code = handler._get_qs_value(qs, 'code')
    state = handler._get_qs_value(qs, 'state')
    if not provider:
        return handler._send_error(400, 'Missing provider parameter')
    if not code:
        return handler._send_error(400, 'Missing code parameter')

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_oauth_callback(provider=provider, code=code, state=state)

    if result.get('status') == 'ok' and result.get('redirect_url'):
        return handler._send_redirect(result['redirect_url'])

    status = handler._status_from_result(result)
    return handler.json(result, status)
