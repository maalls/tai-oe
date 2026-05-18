import http.server

from src.api.server import create_rag_handler


def test_create_rag_handler_routes_prompt_get(monkeypatch):
    handler_class = create_rag_handler({"PORT": 8088, "STORAGE_DIR": "/tmp"})
    handler = handler_class.__new__(handler_class)
    handler.path = "/api/prompt/opportunity/source"

    calls = []

    monkeypatch.setattr(handler, "_handle_prompt_get", lambda parsed_path: calls.append(parsed_path))
    monkeypatch.setattr(http.server.SimpleHTTPRequestHandler, "do_GET", lambda self: calls.append("static"))

    result = handler.do_GET()

    assert result is None
    assert calls == ["/api/prompt/opportunity/source"]


def test_create_rag_handler_falls_back_to_static_get(monkeypatch):
    handler_class = create_rag_handler({"PORT": 8088, "STORAGE_DIR": "/tmp"})
    handler = handler_class.__new__(handler_class)
    handler.path = "/assets/app.js"

    calls = []

    monkeypatch.setattr(handler, "_handle_prompt_get", lambda parsed_path: calls.append(parsed_path))
    monkeypatch.setattr(http.server.SimpleHTTPRequestHandler, "do_GET", lambda self: calls.append("static") or "static-result")

    result = handler.do_GET()

    assert result == "static-result"
    assert calls == ["static"]