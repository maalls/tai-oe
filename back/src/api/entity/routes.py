"""Domain router for entity endpoints."""

import re

from src.api.entity.handler import handle_entity_update_post


def dispatch_entity_routes(handler, method: str, parsed, _qs, _request_handlers) -> bool:
    """Dispatch entity routes across HTTP methods and return True when handled."""
    if method != "POST":
        return False

    entity_update_match = re.match(r"^/api/entity/([^/]+)/([^/]+)$", parsed.path)
    if entity_update_match:
        handle_entity_update_post(handler, entity_update_match)
        return True

    return False
