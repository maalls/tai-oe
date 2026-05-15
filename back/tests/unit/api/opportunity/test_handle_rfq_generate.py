"""Unit tests for OpportunityHandlers.handle_rfq_generate (migrated from RfqHandlers)."""

from pathlib import Path
from src.api.opportunity.handler import OpportunityHandlers

class _EmailServiceStub:
    def __init__(self, email):
        self.email = email
        self.calls = []
    def get_email(self, email_id: str):
        self.calls.append(email_id)
        if isinstance(self.email, Exception):
            raise self.email
        return self.email

class _ServiceFactoryStub:
    def __init__(self, email_service):
        self.email_service = email_service
    def create_email_service(self):
        return self.email_service

class _EmailRepositoryStub:
    class _DbHandler:
        def __init__(self, email):
            self.email = email
            self.calls = []
        def get_email(self, email_id: str):
            self.calls.append(email_id)
            return self.email
    def __init__(self, email):
        self.db_handler = self._DbHandler(email)
    @staticmethod
    def _clean_email_body(text: str, max_length: int = 3000):
        return text[:max_length]

def test_load_email_content_prefers_ddd_email_body():
    email_service = _EmailServiceStub(type("Email", (), {"body": "full body"})())
    handler = OpportunityHandlers(
        service_factory=_ServiceFactoryStub(email_service),
        email_repository=_EmailRepositoryStub({"body_full": "legacy full", "body_preview": "legacy preview"}),
    )
    content = handler._load_email_content("e-1")
    assert content == "full body"
    assert email_service.calls == ["e-1"]
    assert handler.email_repository.db_handler.calls == []

def test_load_email_content_falls_back_to_legacy_preview_when_ddd_body_empty():
    email_service = _EmailServiceStub(type("Email", (), {"body": ""})())
    handler = OpportunityHandlers(
        service_factory=_ServiceFactoryStub(email_service),
        email_repository=_EmailRepositoryStub({"body_full": "", "body_preview": "legacy preview"}),
    )
    content = handler._load_email_content("e-2")
    assert content == "legacy preview"
    assert email_service.calls == ["e-2"]
    assert handler.email_repository.db_handler.calls == ["e-2"]
