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


def handle_document_download(handler, filename, request_handlers, qs=None):
    """Stream document file (PDF, DOCX, etc.)."""
    try:
        qs = qs or {}
        is_inline = qs.get('inline', ['0'])[0] == '1'
        content = request_handlers.handle_get_document_file(filename)

        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        content_type_map = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'txt': 'text/plain; charset=utf-8',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')

        handler.send_response(200)
        handler.send_header('Content-Type', content_type)
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
        return handler._send_error(404, 'Document file not found')
    except Exception as e:
        return handler._send_error(500, f"Error streaming document: {e}")
