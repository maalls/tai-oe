"""Unit tests for OpportunityHandlers.handle_create_opportunity_from_rfp (migrated from RfqHandlers)."""

import pytest
from src.api.opportunity.handler import OpportunityHandlers

class _SupabaseStub:
    def __init__(self):
        self.calls = []
        self.tables = {}
    def table(self, name):
        self.calls.append(('table', name))
        self._last_table = name
        return self
    def select(self, *args, **kwargs):
        self.calls.append(('select', args, kwargs))
        return self
    def eq(self, *args, **kwargs):
        self.calls.append(('eq', args, kwargs))
        return self
    def limit(self, *args, **kwargs):
        self.calls.append(('limit', args, kwargs))
        return self
    class _Result:
        def __init__(self, data):
            self.data = data
        def execute(self):
            return self

    def execute(self):
        self.calls.append(('execute',))
        if getattr(self, '_last_table', None) == 'account':
            return self._Result([{'id': 'acc-1', 'name': 'TestCo'}])
        elif getattr(self, '_last_table', None) == 'opportunity':
            return self._Result([{'id': 'opp-1'}])
        elif getattr(self, '_last_table', None) == 'document':
            return self._Result([{'id': 'doc-1'}])
        elif getattr(self, '_last_table', None) == 'contact':
            return self._Result([{'id': 'contact-1', 'account_id': 'acc-1'}])
        elif getattr(self, '_last_table', None) == 'opportunity_participant':
            return self._Result([{'id': 'part-1'}])
        return self._Result([{'id': 'default'}])

    def insert(self, data):
        self.calls.append(('insert', data))
        if getattr(self, '_last_table', None) == 'account':
            return self._Result([{'id': 'acc-2'}])
        elif getattr(self, '_last_table', None) == 'opportunity':
            return self._Result([{'id': 'opp-2'}])
        elif getattr(self, '_last_table', None) == 'document':
            return self._Result([{'id': 'doc-2'}])
        elif getattr(self, '_last_table', None) == 'contact':
            return self._Result([{'id': 'contact-2'}])
        elif getattr(self, '_last_table', None) == 'opportunity_participant':
            return self._Result([{'id': 'part-2'}])
        return self._Result([{'id': 'default'}])
    def update(self, data):
        self.calls.append(('update', data))
        return self

class _EmailRepositoryStub:
    @staticmethod
    def _clean_email_body(text, max_length=3000):
        return text[:max_length]

class _OpportunityRepositoryStub:
    def _extract_and_enrich_rfp_data(self, text):
        return {'title': 'Test RFP', 'contact': {'company_name': 'TestCo', 'email': 'test@example.com'}}

def test_handle_create_opportunity_from_rfp_success(monkeypatch):
    handler = OpportunityHandlers(
        supabase=_SupabaseStub(),
        email_repository=_EmailRepositoryStub(),
        opportunity_repository=_OpportunityRepositoryStub(),
    )
    handler.get_form = lambda body, content_type: ({'message': 'rfp text', 'file': None}, None)
    # Mock _get_storage_dir to avoid filesystem operations
    class DummyDir:
        def mkdir(self, parents=True, exist_ok=True):
            pass
        def __truediv__(self, other):
            return self
        def write_text(self, text, encoding=None):
            pass
        def write_bytes(self, data):
            pass
    handler._get_storage_dir = lambda source: DummyDir()
    result = handler.handle_create_opportunity_from_rfp(b'body', 'content/type', user_id='user-1')
    assert result['status'] == 'ok'
    assert 'opportunity' in result
    assert 'extracted_rfp' in result

def test_handle_create_opportunity_from_rfp_missing_message_and_file(monkeypatch):
    handler = OpportunityHandlers(
        supabase=_SupabaseStub(),
        email_repository=_EmailRepositoryStub(),
        opportunity_repository=_OpportunityRepositoryStub(),
    )
    handler.get_form = lambda body, content_type: ({'message': '', 'file': None}, None)
    result = handler.handle_create_opportunity_from_rfp(b'body', 'content/type', user_id='user-1')
    assert result['status'] == 'error'
    assert 'Message text or attachment is required' in result['message']
