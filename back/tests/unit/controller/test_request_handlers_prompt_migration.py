"""Unit tests for RequestHandlers prompt helper migration."""

from src.api.router import RequestHandlers


def test_handle_get_prompt_content_reads_prompt_file(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    base = tmp_path / "prompt"
    target = base / "sales" / "prompt.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("hello prompt", encoding="utf-8")

    result = handlers.handle_get_prompt_content("sales", base)

    assert result == "hello prompt"


def test_handle_get_prompt_content_rejects_missing_path(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    base = tmp_path / "prompt"

    try:
        handlers.handle_get_prompt_content("", base)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Missing prompt path"


def test_handle_get_prompt_content_rejects_traversal(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    base = tmp_path / "prompt"
    (tmp_path / "outside").mkdir(parents=True, exist_ok=True)

    try:
        handlers.handle_get_prompt_content("../outside", base)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Invalid prompt path"


def test_handle_get_prompt_content_not_found(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    base = tmp_path / "prompt"

    try:
        handlers.handle_get_prompt_content("unknown", base)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as exc:
        assert str(exc) == "Prompt not found"
