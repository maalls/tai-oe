import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from pathlib import Path

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service, get_database_repository, get_utility_service
from src.api.main import create_app


class _FakeUtilityService:
    def __init__(self, prompt_base_dir: Path):
        self.prompt_base_dir = prompt_base_dir

    def fetch_url(self, target_url: str, max_chars: int, timeout_ms: int) -> dict:
        return {
            "status": 200,
            "ok": True,
            "url": target_url,
            "content_type": "text/plain",
            "truncated": False,
            "text": f"fetch:{max_chars}:{timeout_ms}",
        }

    def curl_request(
        self,
        target_url: str,
        method: str,
        headers: dict[str, str],
        body_text: str | None,
        max_chars: int,
        timeout_ms: int,
    ) -> dict:
        _ = (headers, body_text)
        return {
            "status": 202,
            "ok": True,
            "url": target_url,
            "method": method,
            "content_type": "application/json",
            "truncated": False,
            "text": f"curl:{max_chars}:{timeout_ms}",
        }

    def resolve_fs_path(self, raw_path: str) -> Path:
        if not raw_path:
            raise ValueError("Missing path")
        return Path(raw_path)

    def fs_create(self, target_path: Path, kind: str) -> dict:
        if kind == "file":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch(exist_ok=True)
            return {"status": "ok", "path": str(target_path), "type": "file"}
        target_path.mkdir(parents=True, exist_ok=True)
        return {"status": "ok", "path": str(target_path), "type": "dir"}

    def fs_read(self, target_path: Path, max_chars: int) -> dict:
        content = target_path.read_text(encoding="utf-8")
        return {
            "status": "ok",
            "path": str(target_path),
            "truncated": len(content) > max_chars,
            "text": content[:max_chars],
        }

    def get_prompt_content(self, relative_path: str) -> str:
        if not relative_path:
            raise ValueError("Missing prompt path")
        prompt_path = self.prompt_base_dir / relative_path / "prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError("Prompt not found")
        return prompt_path.read_text(encoding="utf-8")

    def get_email_fetch_loop_status(self) -> dict:
        return {
            "running": False,
            "pid": None,
            "started_at": None,
            "last_heartbeat": None,
            "mode": None,
        }

    def resolve_storage_file(self, raw_filename: str) -> dict:
        if raw_filename == "missing.txt":
            raise FileNotFoundError("Storage file not found")
        return {
            "filename": raw_filename,
            "storage_path": self.prompt_base_dir / "dummy.bin",
            "metadata": {
                "content_type": "text/plain",
                "file_size": 5,
                "content_disposition": "attachment; filename*=UTF-8''dummy.txt",
            },
        }

    def storage_response_headers(self, metadata: dict) -> dict[str, str]:
        return {
            "Content-Type": metadata["content_type"],
            "Content-Length": str(metadata["file_size"]),
            "Accept-Ranges": "bytes",
            "Content-Disposition": metadata["content_disposition"],
        }

    def storage_read_chunks(self, storage_path: Path):
        _ = storage_path
        yield b"hello"

    def storage_not_found_payload(self, raw_filename: str, include_body: bool = False) -> dict:
        payload = {"filename": raw_filename, "content_type": "text/plain"}
        if include_body:
            payload["body"] = b"File not found"
        return payload

    def storage_read_error_payload(self, error: Exception) -> dict:
        _ = error
        return {"content_type": "text/plain", "body": b"Error reading file: x", "message": "x"}


class _FakeAuthServiceValid:
    def verify_token(self, auth_header: str):
        if not auth_header or not auth_header.startswith("Bearer "):
            return False, None
        return True, {"id": "u-admin"}


class _FakeAuthServiceInvalid:
    def verify_token(self, auth_header: str):
        _ = auth_header
        return False, None


class _FakeDatabaseRepositoryAdmin:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


class _FakeDatabaseRepositoryUser:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "user"}


def _client(tmp_path: Path) -> TestClient:
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryAdmin()
    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer valid"})
    return client


def test_fetch_route_returns_payload(tmp_path: Path):
    client = _client(tmp_path)

    response = client.get("/api/fetch?url=https://example.com&max_chars=123&timeout_ms=4567")

    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com"


def test_curl_route_rejects_invalid_method(tmp_path: Path):
    client = _client(tmp_path)

    response = client.post("/api/curl", json={"url": "https://example.com", "method": "TRACE"})

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid method"


def test_fetch_route_requires_valid_token(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceInvalid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryAdmin()
    client = TestClient(app)

    response = client.get("/api/fetch?url=https://example.com")

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_fetch_route_forbidden_for_non_admin_user(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryUser()
    client = TestClient(app)

    response = client.get("/api/fetch?url=https://example.com", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"


def test_fs_create_and_read_routes(tmp_path: Path):
    client = _client(tmp_path)
    target = tmp_path / "tmp" / "sample.txt"

    create_response = client.post("/api/fs/create", json={"path": str(target), "type": "file"})
    target.write_text("bonjour", encoding="utf-8")
    read_response = client.post("/api/fs/read", json={"path": str(target), "max_chars": 10})

    assert create_response.status_code == 200
    assert read_response.status_code == 200
    assert read_response.json()["text"] == "bonjour"


def test_prompt_route_returns_markdown_content(tmp_path: Path):
    prompt_path = tmp_path / "prompts" / "sales" / "intro" / "prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("hello prompt", encoding="utf-8")

    client = _client(tmp_path)
    response = client.get("/api/prompt/sales/intro")

    assert response.status_code == 200
    assert response.text == "hello prompt"


def test_prompt_route_returns_404_when_missing(tmp_path: Path):
    client = _client(tmp_path)

    response = client.get("/api/prompt/unknown/path")

    assert response.status_code == 404
    assert response.json()["error"] == "Prompt not found"


def test_prompt_route_requires_valid_token(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceInvalid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryAdmin()
    client = TestClient(app)

    response = client.get("/api/prompt/sales/intro")

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_prompt_route_forbidden_for_non_admin_user(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    prompt_path = prompt_base_dir / "sales" / "intro" / "prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("hello prompt", encoding="utf-8")

    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryUser()
    client = TestClient(app)

    response = client.get("/api/prompt/sales/intro", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"


def test_email_fetch_loop_status_route_returns_payload(tmp_path: Path):
    client = _client(tmp_path)

    response = client.get("/api/email-fetch-loop/status")

    assert response.status_code == 200
    assert response.json()["running"] is False


def test_email_fetch_loop_status_requires_valid_token(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceInvalid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryAdmin()
    client = TestClient(app)

    response = client.get("/api/email-fetch-loop/status")

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_email_fetch_loop_status_forbidden_for_non_admin_user(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryUser()
    client = TestClient(app)

    response = client.get("/api/email-fetch-loop/status", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 403
    assert response.json()["error"] == "Forbidden"


def test_storage_head_route_returns_headers(tmp_path: Path):
    client = _client(tmp_path)

    response = client.head("/api/storage/dummy.txt")

    assert response.status_code == 200
    assert response.headers["content-length"] == "5"


def test_storage_get_route_returns_content(tmp_path: Path):
    client = _client(tmp_path)

    response = client.get("/api/storage/dummy.txt")

    assert response.status_code == 200
    assert response.content == b"hello"


def test_storage_get_route_returns_404_when_missing(tmp_path: Path):
    client = _client(tmp_path)

    response = client.get("/api/storage/missing.txt")

    assert response.status_code == 404


def test_storage_get_route_requires_valid_token(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceInvalid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryAdmin()
    client = TestClient(app)

    response = client.get("/api/storage/dummy.txt")

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


def test_storage_get_route_allows_non_admin_user(tmp_path: Path):
    prompt_base_dir = tmp_path / "prompts"
    app = create_app()
    app.dependency_overrides[get_utility_service] = lambda: _FakeUtilityService(prompt_base_dir=prompt_base_dir)
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthServiceValid()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDatabaseRepositoryUser()
    client = TestClient(app)

    response = client.get("/api/storage/dummy.txt", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.content == b"hello"
