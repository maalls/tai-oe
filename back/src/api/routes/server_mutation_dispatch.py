"""PATCH and PUT route dispatch for legacy API server."""

import re

from src.api.routes.server_mutation_handlers import handle_action_update_put


def dispatch_patch_request(_handler, _parsed_path: str) -> bool:
    """Dispatch PATCH routes and return True when handled."""
    return False


def dispatch_put_request(handler, parsed_path: str) -> bool:
    """Dispatch PUT routes and return True when handled."""
    update_action_match = re.match(r"^/api/actions/([^/]+)$", parsed_path)
    if update_action_match:
        handle_action_update_put(handler, update_action_match)
        return True

    return False
