"""Storage HEAD/GET handlers for legacy API server."""

import traceback


def handle_storage_head(handler, storage_dir, parsed_path: str):
    """Handle HEAD requests for storage files."""
    raw_filename = parsed_path[len('/api/storage/'):]
    request_handlers = handler.get_request_handlers()
    try:
        storage_info = request_handlers.handle_storage_resolve_file(storage_dir, raw_filename)
    except FileNotFoundError:
        not_found = request_handlers.handle_storage_not_found_payload(raw_filename, include_body=False)
        print(f"[RAG] File not found in any storage location: {not_found['filename']}")
        handler._send_text_response(404, not_found['content_type'])
        return

    filename = storage_info['filename']
    metadata = storage_info['metadata']

    print(f"[RAG] Storage HEAD request for file: {filename}")
    response_headers = request_handlers.handle_storage_response_headers(metadata)

    handler.send_response(200)
    for header_name, header_value in response_headers.items():
        handler.send_header(header_name, header_value)
    handler.end_headers()


def handle_storage_get(handler, storage_dir, parsed_path: str):
    """Handle GET requests for storage files."""
    raw_filename = parsed_path[len('/api/storage/'):]
    request_handlers = handler.get_request_handlers()
    try:
        storage_info = request_handlers.handle_storage_resolve_file(storage_dir, raw_filename)
    except FileNotFoundError:
        not_found = request_handlers.handle_storage_not_found_payload(raw_filename, include_body=True)
        print(f"[RAG] Storage request for file: {not_found['filename']}")
        print(f"[RAG] File not found in any storage location: {not_found['filename']}")
        handler._send_text_response(404, not_found['content_type'], not_found['body'])
        return

    filename = storage_info['filename']
    storage_path = storage_info['storage_path']
    metadata = storage_info['metadata']

    print(f"[RAG] Storage request for file: {filename}")

    try:
        print(f"[RAG] Reading file: {storage_path}")
        response_headers = request_handlers.handle_storage_response_headers(metadata)

        handler.send_response(200)
        for header_name, header_value in response_headers.items():
            handler.send_header(header_name, header_value)
        handler.end_headers()

        # Stream file to avoid truncation issues.
        for chunk in request_handlers.handle_storage_read_chunks(storage_path):
            handler.wfile.write(chunk)
        print(f"[RAG] File sent successfully: {filename} ({metadata['file_size']} bytes)")
        return
    except Exception as error:
        print(f"[RAG] Error reading file {filename}: {error}")
        traceback.print_exc()
        error_payload = request_handlers.handle_storage_read_error_payload(error)
        handler._send_text_response(500, error_payload['content_type'], error_payload['body'])
        return
