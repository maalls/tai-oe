"""File download GET handlers for legacy API server."""


def handle_quote_download(handler, filename, request_handlers, qs=None):
    """Stream PDF quote file."""
    try:
        qs = qs or {}
        is_inline = qs.get('inline', ['0'])[0] == '1'
        content = request_handlers.handle_get_quote_file(filename)
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/pdf')
        disposition = 'inline' if is_inline else 'attachment'
        handler.send_header('Content-Disposition', f'{disposition}; filename="{filename}"')
        handler.send_header('Content-Length', str(len(content)))
        handler.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
        handler.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        handler.send_header('Access-Control-Allow-Credentials', 'true')
        handler._cors_header_sent = True
        handler.end_headers()
        handler.wfile.write(content)
    except FileNotFoundError:
        return handler._send_error(404, 'Quote file not found')
    except Exception as e:
        return handler._send_error(500, f"Error streaming PDF: {e}")
