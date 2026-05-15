"""Unit tests for RequestHandlers email delegation during migration."""

from src.api.router import RequestHandlers


class _ClassifyHandlerStub:
    def __init__(self):
        self.calls = []

    def handle_classify(self, email_uuid: str, user_id: str, force: bool = False):
        self.calls.append((email_uuid, user_id, force))
        return {"status": "ok", "email_id": email_uuid, "force": force}


def test_handle_classify_email_uses_classify_handler(monkeypatch):
    stub = _ClassifyHandlerStub()
    monkeypatch.setattr("src.api.router.ClassifyHandler", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_classify_email("email-1", "u-1", force=True)

    assert result == {"status": "ok", "email_id": "email-1", "force": True}
    assert stub.calls == [("email-1", "u-1", True)]
