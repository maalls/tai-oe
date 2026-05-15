"""Domain router for action endpoints."""

import re

from src.api.action.handler import (
    handle_action_delete,
    handle_action_execute_post,
    handle_action_get,
    handle_action_logs_get,
    handle_action_pause_post,
    handle_action_resume_post,
    handle_action_update_put,
    handle_actions_create_post,
    handle_opportunity_actions_list_get,
)


def dispatch_action_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch action routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        list_actions_match = re.match(r"^/api/opportunities/([^/]+)/actions$", path)
        if list_actions_match:
            handle_opportunity_actions_list_get(handler, list_actions_match, request_handlers)
            return True

        get_action_match = re.match(r"^/api/actions/([^/]+)$", path)
        if get_action_match:
            handle_action_get(handler, get_action_match, request_handlers)
            return True

        get_action_logs_match = re.match(r"^/api/actions/([^/]+)/logs$", path)
        if get_action_logs_match:
            handle_action_logs_get(handler, get_action_logs_match, qs, request_handlers)
            return True

        return False

    if method == "POST":
        if path == '/api/actions':
            handle_actions_create_post(handler)
            return True

        pause_action_match = re.match(r"^/api/actions/([^/]+)/pause$", path)
        if pause_action_match:
            handle_action_pause_post(handler, pause_action_match)
            return True

        resume_action_match = re.match(r"^/api/actions/([^/]+)/resume$", path)
        if resume_action_match:
            handle_action_resume_post(handler, resume_action_match)
            return True

        execute_action_match = re.match(r"^/api/actions/([^/]+)/execute$", path)
        if execute_action_match:
            handle_action_execute_post(handler, execute_action_match)
            return True

        return False

    if method == "PUT":
        update_action_match = re.match(r"^/api/actions/([^/]+)$", path)
        if update_action_match:
            handle_action_update_put(handler, update_action_match)
            return True

        return False

    if method == "DELETE":
        action_delete_match = re.match(r"^/api/actions/([^/]+)$", path)
        if action_delete_match:
            handle_action_delete(handler, action_delete_match)
            return True

        return False

    return False
