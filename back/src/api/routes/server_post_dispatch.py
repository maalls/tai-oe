"""POST route dispatch for legacy API server."""

from src.api.routes.server_post_auth_dispatch import dispatch_post_auth_routes
from src.api.routes.server_post_business_dispatch import dispatch_post_business_routes
from src.api.routes.server_post_core_dispatch import dispatch_post_core_routes
from src.api.routes.server_post_legacy_dispatch import dispatch_post_legacy_and_action_routes
from src.api.routes.server_post_domain_dispatch import dispatch_post_domain_routes


def dispatch_post_request(handler, parsed) -> bool:
    """Dispatch POST routes and return True when handled."""
    if handler._handle_ddd_post_routes(parsed):
        return True

    if dispatch_post_core_routes(handler, parsed.path):
        return True

    if dispatch_post_auth_routes(handler, parsed.path):
        return True

    if dispatch_post_domain_routes(handler, parsed):
        return True

    if dispatch_post_business_routes(handler, parsed):
        return True

    if dispatch_post_legacy_and_action_routes(handler, parsed.path):
        return True

    return False
