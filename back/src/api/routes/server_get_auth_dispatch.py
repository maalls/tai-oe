"""Auth/OAuth GET route dispatch for legacy API server."""

from src.api.auth.routes import dispatch_auth_routes


def dispatch_get_auth_routes(handler, parsed, qs) -> bool:
    """Dispatch auth GET routes and return True when handled."""
    return dispatch_auth_routes(handler, "GET", parsed, qs)
