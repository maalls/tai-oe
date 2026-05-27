"""Reusable API response helpers."""

from __future__ import annotations

from fastapi.responses import JSONResponse


def error_response(message: str, error_code: str, status_code: int = 400) -> JSONResponse:
    """Return the standardized error payload used by business routers."""

    return JSONResponse(
        {
            "status": "error",
            "error_code": error_code,
            "message": message,
        },
        status_code=status_code,
    )
