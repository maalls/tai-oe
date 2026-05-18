"""FastAPI utility router for fetch/curl/fs/prompt endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, PlainTextResponse

from src.api_fastapi.dependencies import get_utility_service
from src.api_fastapi.utils.schemas import CurlRequest, FetchQuery, FsCreateRequest, FsReadRequest
from src.service.utility.utility_service import UtilityService

router = APIRouter(tags=["utils"])


@router.get("/api/fetch")
def fetch_url(
    query: FetchQuery = Depends(),
    utility_service: UtilityService = Depends(get_utility_service),
):
    target_url = str(query.url or "").strip()
    if not target_url:
        return JSONResponse({"error": "Missing url parameter"}, status_code=400)
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        return JSONResponse({"error": "Invalid url scheme"}, status_code=400)

    max_chars = max(100, min(query.max_chars, 50000))
    timeout_ms = max(1000, min(query.timeout_ms, 20000))

    try:
        result = utility_service.fetch_url(target_url=target_url, max_chars=max_chars, timeout_ms=timeout_ms)
        return JSONResponse(result, status_code=200)
    except Exception as exc:
        return JSONResponse({"error": f"Fetch failed: {exc}"}, status_code=500)


@router.post("/api/curl")
def curl_request(
    payload: CurlRequest,
    utility_service: UtilityService = Depends(get_utility_service),
):
    target_url = str(payload.url or "").strip()
    if not target_url:
        return JSONResponse({"error": "Missing url"}, status_code=400)
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        return JSONResponse({"error": "Invalid url scheme"}, status_code=400)

    method = str(payload.method or "GET").upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        return JSONResponse({"error": "Invalid method"}, status_code=400)

    max_chars = max(100, min(payload.max_chars, 50000))
    timeout_ms = max(1000, min(payload.timeout_ms, 20000))

    try:
        result = utility_service.curl_request(
            target_url=target_url,
            method=method,
            headers=payload.headers,
            body_text=payload.body,
            max_chars=max_chars,
            timeout_ms=timeout_ms,
        )
        return JSONResponse(result, status_code=200)
    except Exception as exc:
        return JSONResponse({"error": f"Curl failed: {exc}"}, status_code=500)


@router.post("/api/fs/create")
def fs_create(
    payload: FsCreateRequest,
    utility_service: UtilityService = Depends(get_utility_service),
):
    raw_path = str(payload.path or "").strip()
    kind = payload.type or "dir"

    try:
        target_path = utility_service.resolve_fs_path(raw_path)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    try:
        result = utility_service.fs_create(target_path=target_path, kind=kind)
        return JSONResponse(result, status_code=200)
    except Exception as exc:
        return JSONResponse({"error": f"Create failed: {exc}"}, status_code=500)


@router.post("/api/fs/read")
def fs_read(
    payload: FsReadRequest,
    utility_service: UtilityService = Depends(get_utility_service),
):
    raw_path = str(payload.path or "").strip()
    max_chars = max(100, min(payload.max_chars, 50000))

    try:
        target_path = utility_service.resolve_fs_path(raw_path)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    if not target_path.exists() or not target_path.is_file():
        return JSONResponse({"error": "File not found"}, status_code=404)

    try:
        result = utility_service.fs_read(target_path=target_path, max_chars=max_chars)
        return JSONResponse(result, status_code=200)
    except Exception as exc:
        return JSONResponse({"error": f"Read failed: {exc}"}, status_code=500)


@router.get("/api/prompt/{relative_path:path}")
def get_prompt_content(
    relative_path: str,
    utility_service: UtilityService = Depends(get_utility_service),
):
    try:
        content = utility_service.get_prompt_content(relative_path=relative_path.strip("/"))
        return PlainTextResponse(content=content, media_type="text/plain; charset=utf-8")
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    except Exception as exc:
        return JSONResponse({"error": f"Error reading prompt: {exc}"}, status_code=500)
