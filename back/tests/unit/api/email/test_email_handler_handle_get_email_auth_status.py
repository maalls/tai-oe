"""Tests for EmailHandlers.handle_get_email_auth_status."""

from src.api.email.handler import EmailHandlers


class _AuthStatusServiceStub:
    def __init__(self):
        self.calls = []

    def get_email_auth_status(self, email_id: str, user_id: str):
        self.calls.append((email_id, user_id))
        return {"status": "ok", "data": {"email_id": email_id}}


def test_handle_get_email_auth_status_delegates_to_service():
    handler = EmailHandlers.__new__(EmailHandlers)
    service = _AuthStatusServiceStub()
    handler._auth_status_service = service

    result = handler.handle_get_email_auth_status("e-1", "u-1")

    assert result == {"status": "ok", "data": {"email_id": "e-1"}}
    assert service.calls == [("e-1", "u-1")]
