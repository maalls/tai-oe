"""OpenAI-compatible LLM client."""

import json
import os
import re
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from plain text or fenced code blocks."""
    fence = re.search(r"```(?:json|JSON)?\s*([\s\S]*?)```", text)
    if fence:
        candidate = fence.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            repaired = _balanced_prefix(candidate)
            if repaired:
                try:
                    return json.loads(repaired)
                except Exception:
                    pass
    try:
        return json.loads(text)
    except Exception:
        return None


def _balanced_prefix(text: str) -> Optional[str]:
    """Repair truncated JSON by finding the largest valid JSON prefix with balanced braces/brackets."""
    if not text:
        return None

    stack = []
    in_string = False
    escaped = False
    last_close_pos = -1

    for i, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in '{[':
            stack.append((char, i))
        elif char in '}]':
            if not stack:
                continue
            opening, _ = stack.pop()
            if (char == '}' and opening == '{') or (char == ']' and opening == '['):
                if not stack:
                    last_close_pos = i

    if last_close_pos >= 0:
        candidate = text[:last_close_pos + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
    return None


class LLMClient:
    """Minimal OpenAI-compatible chat completions client using `openai` SDK."""

    def __init__(
        self,
        base_url: str,
        model: str = "local",
        api_key: Optional[str] = None,
        timeout: Optional[float] = 60,
    ):
        self.client = OpenAI(
            base_url=base_url.rstrip("/"),
            api_key=api_key or "sk-local",
            timeout=timeout,
        )
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.timeout is not None:
            params["timeout"] = self.timeout
        if json_mode:
            params["response_format"] = {"type": "json_object"}

        try:
            resp = self.client.chat.completions.create(**params)
            return resp.model_dump() if hasattr(resp, "model_dump") else resp
        except Exception as e:
            error_msg = str(e).lower()
            if json_mode and ("json_object" in error_msg or "json_schema" in error_msg or "response_format" in error_msg):
                print(f"[LLMClient] json_mode not supported, retrying without response_format: {e}")
                params.pop("response_format", None)
                resp = self.client.chat.completions.create(**params)
                return resp.model_dump() if hasattr(resp, "model_dump") else resp
            raise

    def get_content_text(self, data: Dict[str, Any]) -> Optional[str]:
        try:
            choices = data.get("choices") or []
            if not choices:
                return None
            msg = choices[0].get("message")
            if msg and isinstance(msg.get("content"), str):
                return msg["content"]
            text = choices[0].get("text")
            if isinstance(text, str):
                return text
            return None
        except Exception:
            return None

    def ask_json(
        self,
        system_prompt: str,
        user_content: str,
        temperature: float = 0.0,
        max_tokens: int = 20000,
    ) -> Union[Dict[str, Any], str]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        data = self.chat(messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
        content = self.get_content_text(data)
        if isinstance(content, str):
            parsed = extract_json_from_text(content)
            if parsed is not None:
                return parsed
            return content
        return {"raw_response": data}


def get_llm_service() -> LLMClient:
    """Get an LLMClient configured from LLM_URL and LLM_MODEL env vars."""
    llm_url = os.getenv("LLM_URL")
    llm_model = os.getenv("LLM_MODEL")

    if not llm_url:
        raise ImportError("LLM_URL environment variable is not set")
    if not llm_model:
        raise ImportError("LLM_MODEL environment variable is not set")

    normalized_url = llm_url.rstrip("/")
    if not normalized_url.endswith("/v1"):
        normalized_url = f"{normalized_url}/v1"

    return LLMClient(base_url=normalized_url, model=llm_model)


__all__ = ["LLMClient", "extract_json_from_text", "get_llm_service"]
