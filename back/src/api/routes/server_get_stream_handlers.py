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


def handle_source_stream(handler, qs, request_handlers):
    """Stream original Excel source file."""
    try:
        source = (qs.get('source') or [None])[0]
        if not source:
            return handler._send_error(400, "Missing 'source' parameter")
        content = request_handlers.handle_source_raw(qs)
        ext = source.lower().split('.')[-1] if '.' in source else ''
        content_type_map = {
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        handler.send_response(200)
        handler.send_header('Content-Type', content_type)
        handler.send_header('Content-Disposition', f'attachment; filename="{source}"')
        handler.send_header('Content-Length', str(len(content)))
        handler.end_headers()
        handler.wfile.write(content)
    except Exception as e:
        return handler._send_error(500, f"Error streaming source: {e}")

