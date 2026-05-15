"""Unit test for OpportunityHandlers.handle_delete_opportunities."""
from src.api.opportunity.handler import OpportunityHandlers

class _OpportunityRepositoryStub:
    def delete_opportunities(self, opportunity_ids, user_id=None):
        return {'status': 'ok', 'deleted': opportunity_ids, 'user_id': user_id}

def test_handle_delete_opportunities():
    handler = OpportunityHandlers(opportunity_repository=_OpportunityRepositoryStub())
    result = handler.handle_delete_opportunities(['opp-1', 'opp-2'], user_id='user-5')
    assert result['status'] == 'ok'
    assert result['deleted'] == ['opp-1', 'opp-2']
    assert result['user_id'] == 'user-5'
