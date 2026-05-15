"""Legacy and action POST route dispatch for legacy API server."""

import re


def dispatch_action_post_routes(handler, parsed_path: str) -> bool:
    """Dispatch action-specific POST regex routes and return True when handled."""
    pause_action_match = re.match(r"^/api/actions/([^/]+)/pause$", parsed_path)
    if pause_action_match:
        handler._handle_action_pause_post(pause_action_match)
        return True

    resume_action_match = re.match(r"^/api/actions/([^/]+)/resume$", parsed_path)
    if resume_action_match:
        handler._handle_action_resume_post(resume_action_match)
        return True

    execute_action_match = re.match(r"^/api/actions/([^/]+)/execute$", parsed_path)
    if execute_action_match:
        handler._handle_action_execute_post(execute_action_match)
        return True

    return False


def dispatch_post_legacy_and_action_routes(handler, parsed_path: str) -> bool:
    """Dispatch remaining legacy/action POST routes and return True when handled."""
    if parsed_path == '/api/csv/source':
        handler._handle_csv_source_post()
        return True

    if parsed_path == '/api/rfp':
        handler._handle_rfp_post()
        return True

    if parsed_path == '/api/quote':
        handler._handle_quote_submit_post()
        return True

    if parsed_path == '/api/quote/send':
        handler._handle_quote_send_post()
        return True

    if parsed_path == '/api/actions':
        handler._handle_actions_create_post()
        return True

    return dispatch_action_post_routes(handler, parsed_path)
