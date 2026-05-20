"""Utilities to run PDF extraction with vision-capable LLMs."""

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any

from src.infrastructure.clients.llm import extract_json_from_text


def _format_exception_chain(exc: Exception) -> str:
    """Format exception and chained causes for diagnostic logs/API responses."""
    parts: list[str] = []
    cursor: Exception | None = exc
    seen = 0
    while cursor is not None and seen < 5:
        parts.append(f"{cursor.__class__.__name__}: {cursor}")
        next_cursor = cursor.__cause__ or cursor.__context__
        cursor = next_cursor if isinstance(next_cursor, Exception) else None
        seen += 1
    return " <- ".join(parts)


def _llm_request_context(llm_client: Any) -> str:
    """Return safe LLM request context for diagnostics."""
    model = getattr(llm_client, "model", "unknown")
    client = getattr(llm_client, "client", None)
    base_url = getattr(client, "base_url", None)
    timeout = getattr(llm_client, "timeout", None)
    base_url_text = str(base_url) if base_url is not None else "unknown"
    return f"model={model}, base_url={base_url_text}, timeout={timeout}"


def _render_pdf_to_image_data_urls(
    pdf_path: Path,
    image_scale: float = 2.0,
    image_format: str = "JPEG",
    image_quality: int = 90,
) -> list[str]:
    """Render each PDF page into a base64 data URL."""
    try:
        import pypdfium2 as pdfium
    except Exception as exc:
        raise RuntimeError(f"Failed to import pypdfium2 for vision parsing: {exc}")

    pdf_doc = pdfium.PdfDocument(str(pdf_path))
    if len(pdf_doc) == 0:
        raise ValueError(f"Empty PDF document: {pdf_path}")

    urls: list[str] = []
    mime = image_format.lower()
    if mime == "jpg":
        mime = "jpeg"

    for page_index in range(len(pdf_doc)):
        page = pdf_doc[page_index]
        image = page.render(scale=image_scale).to_pil()
        buf = BytesIO()
        image.save(buf, format=image_format, quality=image_quality)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        urls.append(f"data:image/{mime};base64,{encoded}")

    return urls


def _extract_content_text(llm_client: Any, data: dict[str, Any]) -> str | None:
    """Extract textual content from a chat completion payload."""
    if hasattr(llm_client, "get_content_text"):
        content = llm_client.get_content_text(data)
        if isinstance(content, str):
            return content

    choices = data.get("choices") if isinstance(data, dict) else None
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            return msg.get("content")

    return None


def extract_from_pdf_with_vision(
    pdf_path: str | Path,
    llm_client: Any,
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 12000,
    image_scale: float = 2.0,
    image_format: str = "JPEG",
    image_quality: int = 90,
    json_response: bool = True,
) -> dict[str, Any]:
    """Extract structured JSON from a PDF by sending rendered pages to a vision-capable LLM."""
    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if not hasattr(llm_client, "client") or not hasattr(llm_client, "model"):
        raise RuntimeError("LLM client does not support vision calls")

    data_urls = _render_pdf_to_image_data_urls(
        path,
        image_scale=image_scale,
        image_format=image_format,
        image_quality=image_quality,
    )

    user_blocks: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
    user_blocks.extend(
        {"type": "image_url", "image_url": {"url": image_url}}
        for image_url in data_urls
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_blocks},
    ]

    params: dict[str, Any] = {
        "model": llm_client.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_response:
        params["response_format"] = {"type": "json_object"}

    try:
        resp = llm_client.client.chat.completions.create(**params)
    except Exception as first_exc:
        if not json_response:
            context = _llm_request_context(llm_client)
            details = _format_exception_chain(first_exc)
            raise RuntimeError(f"Vision LLM request failed ({context}): {details}") from first_exc

        params.pop("response_format", None)
        try:
            resp = llm_client.client.chat.completions.create(**params)
        except Exception as second_exc:
            context = _llm_request_context(llm_client)
            details = _format_exception_chain(second_exc)
            raise RuntimeError(f"Vision LLM request failed ({context}): {details}") from second_exc

    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    if not isinstance(payload, dict):
        raise RuntimeError("Vision model response is not a mapping")

    content = _extract_content_text(llm_client, payload)
    if not isinstance(content, str):
        raise RuntimeError("Vision model response has no text content")

    parsed = extract_json_from_text(content)
    if isinstance(parsed, dict):
        return parsed

    try:
        decoded = json.loads(content)
    except Exception as exc:
        raise RuntimeError(f"Vision model did not return valid JSON: {exc}")

    if not isinstance(decoded, dict):
        raise RuntimeError("Vision model returned JSON but not an object")

    return decoded
