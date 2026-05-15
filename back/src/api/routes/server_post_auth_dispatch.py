"""Auth POST route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.auth.routes import dispatch_auth_routes


def dispatch_post_auth_routes(handler, parsed_path: str) -> bool:
    """Dispatch auth POST routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    return dispatch_auth_routes(handler, "POST", parsed, {})
