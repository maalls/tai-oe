"""Unit test for OpportunityHandlers.handle_generate_quote_for_opportunity."""
from src.api.opportunity.handler import OpportunityHandlers

class _OpportunityRepositoryStub:
    def handle_generate_quote_for_opportunity(self, opportunity_id, user_id=None):
        return {'status': 'ok', 'opportunity_id': opportunity_id, 'user_id': user_id}

def test_handle_generate_quote_for_opportunity():
    handler = OpportunityHandlers(opportunity_repository=_OpportunityRepositoryStub())
    result = handler.handle_generate_quote_for_opportunity('opp-2', user_id='user-2')
    assert result['status'] == 'ok'
    assert result['opportunity_id'] == 'opp-2'
    assert result['user_id'] == 'user-2'
