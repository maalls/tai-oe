import json
import os
import time
import hashlib
from pathlib import Path
from sys import argv
from typing import Any, Dict, Optional

from src.infrastructure.clients.llm import LLMClient, extract_json_from_text
from src.infrastructure.llm_factory import LLMClientFactory


def _get_back_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_prompt_file(filename: str) -> Path:
    candidates = [
        Path(__file__).resolve().parent / filename,
        _get_back_root() / "src" / "text" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Prompt file not found: {candidates[0]}")


def _cache_llm_extraction(content: str, payload: Dict[str, Any], elapsed: float) -> None:
    """Persist LLM extraction payload for debugging and traceability."""
    try:
        project_root = _get_back_root()
        cache_dir = project_root / "var" / "llm" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()[:16]
        ts = time.strftime("%Y%m%d-%H%M%S")
        cache_file = cache_dir / f"rfp_extract_{ts}_{digest}.json"

        envelope = {
            "cached_at": ts,
            "elapsed_seconds": round(elapsed, 3),
            "input_chars": len(content),
            "result": payload,
        }
        cache_file.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[TextReader] Cache write failed: {e}")

def extract_rfp_from_email(
    email_path: str = "request/email.txt"
) -> Dict[str, Any]:
    if not email_path:
        raise FileNotFoundError("Email path required")

    candidate = Path(email_path)

    if not candidate.exists():
        raise FileNotFoundError(f"Email file not found: {candidate}")

    content = candidate.read_text(encoding="utf-8")

    return extract_rfp_from_text(content)

def extract_company_from_text(content: str) -> Dict[str, Any]:
    prompt_file = _resolve_prompt_file("company_prompt.md")
    system_prompt = prompt_file.read_text(encoding="utf-8").strip()

    client = LLMClientFactory().create_client()
    resp = client.ask_json(system_prompt=system_prompt, user_content=content)

    return resp

def extract_rfp_from_text(content: str, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
    # Truncate content to fit within LLM context window (4096 tokens)
    # Roughly 1 token ≈ 4 characters, so ~1500 chars ≈ 375 tokens max (leaves headroom)
    MAX_CONTENT_LENGTH = 20000

    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH] + "..."
        print(f"[TextReader] Content truncated to {MAX_CONTENT_LENGTH} chars for LLM processing")

    prompt_file = _resolve_prompt_file("prompt.md")
    system_prompt = prompt_file.read_text(encoding="utf-8").strip()

	
    print(f"[TextReader] Extracting RFP data using LLM with text {content}")
    # Use reusable LLM client
    # Normalize llm_url for OpenAI SDK: it expects base_url ending with /v1
    if timeout_seconds is None:
        llm_timeout = int(os.getenv("LLM_TIMEOUT", "45"))
    else:
        llm_timeout = int(timeout_seconds)
    if llm_timeout <= 0:
        llm_timeout = None
    llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1200"))
    client = LLMClientFactory().create_client(timeout=llm_timeout)

    started_at = time.time()
    try:
        rfp_data = client.ask_json(
            system_prompt=system_prompt,
            user_content=content,
            max_tokens=llm_max_tokens,
        )
    except Exception as e:
        elapsed = time.time() - started_at
        timeout_label = "none" if llm_timeout is None else f"{llm_timeout}s"
        raise RuntimeError(
            f"LLM extraction failed after {elapsed:.1f}s (timeout={timeout_label}): {e}"
        ) from e

    elapsed = time.time() - started_at
    print(f"[TextReader] Raw RFP data extracted in {elapsed:.1f}s: {rfp_data}")
    if isinstance(rfp_data, list):
        print(f"[BusinessHandlers] RFP data is a list, wrapping as products")
        rfp_data = {"products": rfp_data, "contact": {}}
    elif isinstance(rfp_data, str):
        print(f"[BusinessHandlers] RFP data is a string, attempting to parse")
        try:
            parsed = json.loads(rfp_data)
            if isinstance(parsed, dict):
                rfp_data = parsed
            elif isinstance(parsed, list):
                rfp_data = {"products": parsed, "contact": {}}
            else:
                rfp_data = {"contact": {}}
        except Exception:
            rfp_data = {"contact": {}}
    elif not isinstance(rfp_data, dict):
        print(f"[BusinessHandlers] RFP data is not a dict: {type(rfp_data)}")
        rfp_data = {"contact": {}}

    _cache_llm_extraction(content=content, payload=rfp_data, elapsed=elapsed)

    return rfp_data


if __name__ == "__main__":
    try:
        # get email path from user script argument, not from os environment
        if len(argv) > 1:
            email_path_env = argv[1]
        else:
            raise ValueError("Email path argument required")

        result = extract_rfp_from_email(email_path=email_path_env)
        # If we got raw text with fenced JSON, pretty-print parsed JSON; else pretty-print result
        if isinstance(result, dict) and "raw" in result and isinstance(result["raw"], str):
            parsed = extract_json_from_text(result["raw"])
            if parsed is not None:
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            else:
                print(result["raw"])  # print raw string
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}")

