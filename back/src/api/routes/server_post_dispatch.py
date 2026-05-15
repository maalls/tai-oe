"""POST route dispatch for legacy API server."""


def dispatch_post_request(handler, parsed) -> bool:
    """Dispatch POST routes and return True when handled."""
    if handler._handle_ddd_post_routes(parsed):
        return True

    if handler._handle_post_core_routes(parsed.path):
        return True

    if handler._handle_post_auth_routes(parsed.path):
        return True

    if handler._handle_post_domain_routes(parsed):
        return True

    if handler._handle_post_opportunity_quote_invoice_routes(parsed):
        return True

    if handler._handle_post_legacy_and_action_routes(parsed.path):
        return True

    return False
