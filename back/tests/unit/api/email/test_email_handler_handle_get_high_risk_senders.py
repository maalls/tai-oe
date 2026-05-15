"""Tests for EmailHandlers.handle_get_high_risk_senders."""

from src.api.email.handler import EmailHandlers


class _AuthStatusServiceStub:
    def __init__(self):
        self.calls = []

    def get_high_risk_senders(self, user_id: str):
        self.calls.append(user_id)
        return {"status": "ok", "data": [], "total": 0}


def test_handle_get_high_risk_senders_delegates_to_service():
    handler = EmailHandlers.__new__(EmailHandlers)
    service = _AuthStatusServiceStub()
    handler._auth_status_service = service

    result = handler.handle_get_high_risk_senders("u-1")

    assert result == {"status": "ok", "data": [], "total": 0}
    assert service.calls == ["u-1"]
