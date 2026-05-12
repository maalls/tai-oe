"""Multipart form data parsing utilities."""

from typing import Optional, Tuple


def parse_multipart(body: bytes, boundary: str) -> Tuple[Optional[str], Optional[bytes]]:
    """Parse multipart form data and extract filename and file content.
    
    Args:
        body: Raw request body bytes
        boundary: Multipart boundary string from Content-Type header
        
    Returns:
        (filename, file_data) or (None, None) if not found
    """
    boundary_bytes = f'--{boundary}'.encode()
    parts = body.split(boundary_bytes)

    for part in parts:
        if b'Content-Disposition' in part:
            # Find filename in Content-Disposition header
            disp_end = part.find(b'\r\n\r\n')
            if disp_end > 0:
                headers = part[:disp_end].decode('utf-8', errors='ignore')
                if 'filename=' in headers:
                    # Extract filename
                    filename_start = headers.find('filename="') + len('filename="')
                    filename_end = headers.find('"', filename_start)
                    filename = headers[filename_start:filename_end]

                    # Extract file content (between headers and next boundary)
                    content_start = disp_end + 4
                    content_end = part.rfind(b'\r\n')
                    if content_end < content_start:
                        content_end = len(part)
                    file_data = part[content_start:content_end]

                    return filename, file_data

    return None, None


def extract_boundary_from_header(content_type: str) -> Optional[str]:
    """Extract multipart boundary from Content-Type header.
    
    Args:
        content_type: Content-Type header value
        
    Returns:
        Boundary string or None if not found
    """
    for part in content_type.split(';'):
        if 'boundary=' in part:
            return part.split('=')[1].strip()
    return None
