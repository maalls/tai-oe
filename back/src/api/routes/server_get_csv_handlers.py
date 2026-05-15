"""CSV GET handlers for legacy API server."""


def handle_csv_get(handler, parsed_path: str, qs):
    """Handle /api/csv* GET endpoints."""
    request_handlers = handler.get_request_handlers()

    if parsed_path == '/api/csv/files':
        return handle_csv_files_get(handler, qs, request_handlers)
    if parsed_path == '/api/csv/preview':
        return handle_csv_preview_get(handler, qs, request_handlers)
    if parsed_path == '/api/csv/raw':
        return handler._handle_raw_stream(qs, request_handlers)
    if parsed_path == '/api/csv/source':
        return handler._handle_source_stream(qs, request_handlers)
    if parsed_path == '/api/csv/download':
        return handler._handle_csv_download(qs, request_handlers)
    if parsed_path == '/api/csv/sources':
        return handle_csv_sources_get(handler, request_handlers)
    if parsed_path == '/api/csv/query':
        return handle_csv_query_get(handler, qs, request_handlers)
    if parsed_path.startswith('/api/csv/search'):
        return handle_csv_search_get(handler, qs, request_handlers)

    return None


def handle_csv_files_get(handler, qs, request_handlers):
    """Handle /api/csv/files GET endpoint."""
    return handler.json(request_handlers.handle_list_files(qs))


def handle_csv_preview_get(handler, qs, request_handlers):
    """Handle /api/csv/preview GET endpoint."""
    return handler.json(request_handlers.handle_preview(qs))


def handle_csv_sources_get(handler, request_handlers):
    """Handle /api/csv/sources GET endpoint."""
    return handler.json(request_handlers.handle_sources())


def handle_csv_query_get(handler, qs, request_handlers):
    """Handle /api/csv/query GET endpoint."""
    return handler.json(request_handlers.handle_query(qs))


def handle_csv_search_get(handler, qs, request_handlers):
    """Handle /api/csv/search* GET endpoints."""
    return handler.json(request_handlers.handle_search(qs, handler.get_embedding_generator()))
