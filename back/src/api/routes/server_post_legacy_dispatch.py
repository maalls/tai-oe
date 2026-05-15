"""Legacy and action POST route dispatch for legacy API server."""

import re

from src.api.action.handler import (
    handle_action_execute_post,
    handle_action_pause_post,
    handle_action_resume_post,
    handle_actions_create_post,
)
from src.api.csv.handler import handle_csv_source_post
from src.api.quote.handler import handle_quote_send_post, handle_quote_submit_post
from src.api.rfq.handler import handle_rfp_post


def dispatch_action_post_routes(handler, parsed_path: str) -> bool:
    """Dispatch action-specific POST regex routes and return True when handled."""
    pause_action_match = re.match(r"^/api/actions/([^/]+)/pause$", parsed_path)
    if pause_action_match:
        handle_action_pause_post(handler, pause_action_match)
        return True

    resume_action_match = re.match(r"^/api/actions/([^/]+)/resume$", parsed_path)
    if resume_action_match:
        handle_action_resume_post(handler, resume_action_match)
        return True

    execute_action_match = re.match(r"^/api/actions/([^/]+)/execute$", parsed_path)
    if execute_action_match:
        handle_action_execute_post(handler, execute_action_match)
        return True

    return False


def dispatch_post_legacy_and_action_routes(handler, parsed_path: str) -> bool:
    """Dispatch remaining legacy/action POST routes and return True when handled."""
    if parsed_path == '/api/csv/source':
        handle_csv_source_post(handler)
        return True

    if parsed_path == '/api/rfp':
        handle_rfp_post(handler)
        return True

    if parsed_path == '/api/quote':
        handle_quote_submit_post(handler)
        return True

    if parsed_path == '/api/quote/send':
        handle_quote_send_post(handler)
        return True

    if parsed_path == '/api/actions':
        handle_actions_create_post(handler)
        return True

    return dispatch_action_post_routes(handler, parsed_path)
