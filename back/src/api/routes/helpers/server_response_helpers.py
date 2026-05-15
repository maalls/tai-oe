"""HTTP response helpers for legacy API server."""

import json


def send_json(handler, payload, status_code=200):
    """Send JSON response."""
    try:
        data = json.dumps(payload).encode('utf-8')
        handler.send_response(status_code)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Content-Length', str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        return
    except Exception as error:
        try:
            send_error(handler, 500, f"Error serializing JSON: {error}")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return


def send_error(handler, code: int, message: str):
    """Send error response."""
    try:
        payload = json.dumps({"error": message}).encode('utf-8')
        handler.send_response(code)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Content-Length', str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        return


def send_text_response(handler, code: int, content_type: str, body: bytes = None):
    """Send plain text/binary response payload."""
    try:
        handler.send_response(code)
        handler.send_header('Content-Type', content_type)
        if body is not None:
            handler.send_header('Content-Length', str(len(body)))
        handler.end_headers()
        if body is not None:
            handler.wfile.write(body)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        return


def send_redirect(handler, location: str, code: int = 302):
    """Send HTTP redirect response."""
    try:
        handler.send_response(code)
        handler.send_header('Location', location)
        handler.end_headers()
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        return
