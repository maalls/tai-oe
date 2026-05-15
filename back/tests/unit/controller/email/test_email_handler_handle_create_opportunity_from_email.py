"""Tests for EmailHandlers.handle_create_opportunity_from_email."""

from src.controller.email_handler import EmailHandlers


class _RepositoryStub:
    def __init__(self):
        self.calls = []

    def create_opportunity_from_email(self, message_id: str, user_id: str = None):
        self.calls.append((message_id, user_id))
        return {"status": "ok", "opportunity": {"id": "opp-1"}}


def test_handle_create_opportunity_from_email_delegates_to_repository():
    handler = EmailHandlers.__new__(EmailHandlers)
    handler._repository = _RepositoryStub()

    result = handler.handle_create_opportunity_from_email("email-42", "u-1")

    assert result == {"status": "ok", "opportunity": {"id": "opp-1"}}
    assert handler._repository.calls == [("email-42", "u-1")]