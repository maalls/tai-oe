"""GET route dispatch for legacy API server."""

from src.api.routes.server_get_misc_dispatch import dispatch_get_misc_routes
from src.api.routes.server_get_auth_dispatch import dispatch_get_auth_routes
from src.api.routes.server_get_mail_dispatch import dispatch_get_mail_routes
from src.api.routes.server_get_data_dispatch import dispatch_get_data_routes
from src.api.routes.server_get_action_download_dispatch import dispatch_get_action_download_routes


def dispatch_get_request(handler, parsed, qs) -> bool:
    """Dispatch GET routes and return True when handled."""
    if handler._handle_ddd_get_routes(parsed, qs):
        return True

    if dispatch_get_misc_routes(handler, parsed, qs):
        return True

    if dispatch_get_auth_routes(handler, parsed, qs):
        return True

    if dispatch_get_mail_routes(handler, parsed, qs):
        return True

    request_handlers = handler.request_handlers
    if dispatch_get_data_routes(handler, parsed, qs, request_handlers):
        return True

    if dispatch_get_action_download_routes(handler, parsed, qs, request_handlers):
        return True

    return False
