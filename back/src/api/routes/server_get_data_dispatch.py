"""Data GET route dispatch for legacy API server."""


def dispatch_get_data_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch csv/quotes/opportunity search GET routes and return True when handled."""
    if parsed.path.startswith('/api/csv'):
        handler._handle_csv_get(parsed.path, qs)
        return True

    if parsed.path == '/api/quotes/list':
        handler._handle_quotes_list_get(request_handlers)
        return True

    if parsed.path == '/api/opportunities/search':
        handler._handle_opportunities_search_get(qs, request_handlers)
        return True

    return False
