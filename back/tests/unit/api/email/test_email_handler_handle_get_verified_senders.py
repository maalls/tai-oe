"""Tests for EmailHandlers.handle_get_verified_senders."""

from src.api.email.handler import EmailHandlers


class _AuthStatusServiceStub:
    def __init__(self):
        self.calls = []

    def get_verified_senders(self, user_id: str):
        self.calls.append(user_id)
        return {"status": "ok", "data": [{"sender_email": "safe@example.com"}], "total": 1}


def test_handle_get_verified_senders_delegates_to_service():
    handler = EmailHandlers.__new__(EmailHandlers)
    service = _AuthStatusServiceStub()
    handler._auth_status_service = service

    result = handler.handle_get_verified_senders("u-1")

    assert result == {"status": "ok", "data": [{"sender_email": "safe@example.com"}], "total": 1}
    assert service.calls == ["u-1"]
