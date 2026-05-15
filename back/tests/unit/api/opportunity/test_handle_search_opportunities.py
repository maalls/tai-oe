"""Unit test for OpportunityHandlers.handle_search_opportunities."""
from src.api.opportunity.handler import OpportunityHandlers

class _OpportunityRepositoryStub:
    def search_opportunities(self, user_id, source_reference_id=None, name=None):
        return {'status': 'ok', 'user_id': user_id, 'source_reference_id': source_reference_id, 'name': name}

def test_handle_search_opportunities():
    handler = OpportunityHandlers(opportunity_repository=_OpportunityRepositoryStub())
    result = handler.handle_search_opportunities('user-4', source_reference_id='src-1', name='OppName')
    assert result['status'] == 'ok'
    assert result['user_id'] == 'user-4'
    assert result['source_reference_id'] == 'src-1'
    assert result['name'] == 'OppName'
