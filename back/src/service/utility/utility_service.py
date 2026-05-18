"""Service for HTTP and filesystem utility operations."""

import json
import os
from pathlib import Path
from typing import Any, Iterator
import urllib.parse
import urllib.request


class UtilityService:
    """Expose utility operations used by API transport layers."""

    def __init__(self, base_dir: Path, prompt_base_dir: Path):
        self.base_dir = base_dir
        self.prompt_base_dir = prompt_base_dir

    def _resolve_storage_dirs(self) -> list[Path]:
        configured = os.environ.get("STORAGE_DIR")
        candidates: list[Path] = []

        if configured:
            configured_path = Path(configured)
            if not configured_path.is_absolute():
                candidates.append((self.base_dir / configured_path).resolve())
                candidates.append((self.base_dir / "back" / configured_path).resolve())
            else:
                candidates.append(configured_path.resolve())

        candidates.extend(
            [
                (self.base_dir / "back" / "var" / "storage").resolve(),
                (self.base_dir / "var" / "storage").resolve(),
            ]
        )

        deduplicated: list[Path] = []
        for candidate in candidates:
            if candidate not in deduplicated:
                deduplicated.append(candidate)
        return deduplicated

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

    def get_email_fetch_loop_status(self) -> dict[str, Any]:
        status_path = self.base_dir / "var" / "email_fetch_loop.json"
        legacy_path = self.base_dir / "back" / "var" / "email_fetch_loop.json"

        if not status_path.exists() and legacy_path.exists():
            status_path = legacy_path

        if not status_path.exists():
            return {
                "running": False,
                "pid": None,
                "started_at": None,
                "last_heartbeat": None,
                "mode": None,
            }

        try:
            payload = json.loads(status_path.read_text(encoding="utf-8") or "{}")
        except Exception:
            payload = {}

        pid = payload.get("pid")
        running = False
        if pid:
            try:
                os.kill(int(pid), 0)
                running = True
            except Exception:
                running = False

        return {
            "running": running,
            "pid": pid,
            "started_at": payload.get("started_at"),
            "last_heartbeat": payload.get("last_heartbeat"),
            "mode": payload.get("mode"),
        }

    def find_storage_path(self, filename: str) -> Path | None:
        storage_subdirs = ["rfp_uploads", "attachment", "attachments", "email", "quotes"]

        for storage_dir in self._resolve_storage_dirs():
            for subdir in storage_subdirs:
                candidate = storage_dir / subdir / filename
                if candidate.exists():
                    return candidate

            root_candidate = storage_dir / filename
            if root_candidate.exists():
                return root_candidate

        return None

    def storage_file_metadata(self, filename: str, storage_path: Path) -> dict[str, Any]:
        file_ext = storage_path.suffix.lower()
        content_type_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain; charset=utf-8",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".zip": "application/zip",
        }
        content_type = content_type_map.get(file_ext, "application/octet-stream")
        file_size = storage_path.stat().st_size
        encoded_filename = urllib.parse.quote(filename)
        disposition = "inline" if content_type == "application/pdf" else "attachment"

        return {
            "content_type": content_type,
            "file_size": file_size,
            "content_disposition": f"{disposition}; filename*=UTF-8''{encoded_filename}",
        }

    def resolve_storage_file(self, raw_filename: str) -> dict[str, Any]:
        filename = self.sanitize_storage_filename(raw_filename)
        storage_path = self.find_storage_path(filename)
        if not storage_path or not storage_path.exists():
            raise FileNotFoundError(f"Storage file not found: {filename}")

        metadata = self.storage_file_metadata(filename, storage_path)
        return {
            "filename": filename,
            "storage_path": storage_path,
            "metadata": metadata,
        }

    def storage_read_chunks(self, storage_path: Path, chunk_size: int = 8192) -> Iterator[bytes]:
        with open(storage_path, "rb") as file_handle:
            while True:
                chunk = file_handle.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @staticmethod
    def storage_response_headers(metadata: dict[str, Any]) -> dict[str, str]:
        return {
            "Content-Type": metadata["content_type"],
            "Content-Length": str(metadata["file_size"]),
            "Accept-Ranges": "bytes",
            "Content-Disposition": metadata["content_disposition"],
        }

    def storage_not_found_payload(self, raw_filename: str, include_body: bool = False) -> dict[str, Any]:
        filename = self.sanitize_storage_filename(raw_filename)
        payload: dict[str, Any] = {
            "filename": filename,
            "content_type": "text/plain",
        }
        if include_body:
            payload["body"] = b"File not found"
        return payload

    @staticmethod
    def storage_read_error_payload(error: Exception) -> dict[str, Any]:
        message = f"Error reading file: {str(error)}"
        return {
            "content_type": "text/plain",
            "body": message.encode("utf-8"),
            "message": message,
        }

    @staticmethod
    def sanitize_storage_filename(raw_filename: str) -> str:
        filename = urllib.parse.unquote(raw_filename)
        return filename.replace("..", "").replace("/", "")
