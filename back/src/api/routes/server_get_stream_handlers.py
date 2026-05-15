"""Streaming GET handlers for legacy API server."""


def handle_raw_stream(handler, qs, request_handlers):
    """Stream raw CSV file."""
    try:
        content = request_handlers.handle_raw(qs)
        handler.send_response(200)
        handler.send_header('Content-Type', 'text/csv; charset=utf-8')
        handler.send_header('Content-Length', str(len(content)))
        handler.end_headers()
        handler.wfile.write(content)
    except Exception as e:
        return handler._send_error(500, f"Error streaming CSV: {e}")

