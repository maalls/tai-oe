"""Service for HTTP and filesystem utility operations."""

from pathlib import Path
from typing import Any
import urllib.parse
import urllib.request


class UtilityService:
    """Expose utility operations used by API transport layers."""

    def __init__(self, base_dir: Path, prompt_base_dir: Path):
        self.base_dir = base_dir
        self.prompt_base_dir = prompt_base_dir

    def fetch_url(self, target_url: str, max_chars: int, timeout_ms: int) -> dict[str, Any]:
        with urllib.request.urlopen(target_url, timeout=timeout_ms / 1000) as resp:
            content_type = resp.headers.get("Content-Type", "")
            status = getattr(resp, "status", 200)
            raw = resp.read()

        text = raw.decode("utf-8", errors="replace")
        truncated = text[:max_chars]
        return {
            "status": status,
            "ok": 200 <= status < 300,
            "url": target_url,
            "content_type": content_type,
            "truncated": len(text) > max_chars,
            "text": truncated,
        }

    def curl_request(
        self,
        target_url: str,
        method: str,
        headers: dict[str, str],
        body_text: str | None,
        max_chars: int,
        timeout_ms: int,
    ) -> dict[str, Any]:
        data_bytes = body_text.encode("utf-8") if body_text is not None else None
        req = urllib.request.Request(target_url, data=data_bytes, method=method)
        for key, value in headers.items():
            if isinstance(key, str) and isinstance(value, str):
                req.add_header(key, value)

        with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
            content_type = resp.headers.get("Content-Type", "")
            status = getattr(resp, "status", 200)
            raw = resp.read()

        text = raw.decode("utf-8", errors="replace")
        truncated = text[:max_chars]
        return {
            "status": status,
            "ok": 200 <= status < 300,
            "url": target_url,
            "content_type": content_type,
            "truncated": len(text) > max_chars,
            "text": truncated,
        }

    def resolve_fs_path(self, raw_path: str) -> Path:
        if not raw_path:
            raise ValueError("Missing path")

        input_path = Path(raw_path)
        if raw_path.startswith("~"):
            raw_path = raw_path[1:].lstrip("/")
            input_path = Path(raw_path)

        if input_path.is_absolute():
            try:
                input_path = input_path.relative_to(self.base_dir)
            except Exception as exc:
                raise ValueError("Invalid path") from exc

        target_path = (self.base_dir / input_path).resolve()
        if self.base_dir not in target_path.parents and target_path != self.base_dir:
            raise ValueError("Invalid path")

        return target_path

    def fs_create(self, target_path: Path, kind: str) -> dict[str, Any]:
        if kind == "file":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch(exist_ok=True)
            if not target_path.exists() or not target_path.is_file():
                raise RuntimeError("file not created")
            return {"status": "ok", "path": str(target_path), "type": "file"}

        target_path.mkdir(parents=True, exist_ok=True)
        if not target_path.exists() or not target_path.is_dir():
            raise RuntimeError("directory not created")
        return {"status": "ok", "path": str(target_path), "type": "dir"}

    def fs_read(self, target_path: Path, max_chars: int) -> dict[str, Any]:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        truncated = content[:max_chars]
        return {
            "status": "ok",
            "path": str(target_path),
            "truncated": len(content) > max_chars,
            "text": truncated,
        }

    def get_prompt_content(self, relative_path: str) -> str:
        if not relative_path:
            raise ValueError("Missing prompt path")

        prompt_path = (self.prompt_base_dir / relative_path / "prompt.md").resolve()
        if self.prompt_base_dir not in prompt_path.parents:
            raise ValueError("Invalid prompt path")
        if not prompt_path.exists():
            raise FileNotFoundError("Prompt not found")

        return prompt_path.read_text(encoding="utf-8")

    @staticmethod
    def sanitize_storage_filename(raw_filename: str) -> str:
        filename = urllib.parse.unquote(raw_filename)
        return filename.replace("..", "").replace("/", "")
