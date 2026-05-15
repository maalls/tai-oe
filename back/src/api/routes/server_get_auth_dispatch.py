"""Auth/OAuth GET route dispatch for legacy API server."""


def dispatch_get_auth_routes(handler, parsed, qs) -> bool:
    """Dispatch auth GET routes and return True when handled."""
    if parsed.path == '/api/auth/user':
        handler._handle_auth_user_get()
        return True

    if parsed.path == '/api/oauth/login':
        handler._handle_oauth_login_get(qs)
        return True

    if parsed.path == '/api/oauth/callback':
        handler._handle_oauth_callback_get(qs)
        return True

    return False
