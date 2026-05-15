"""Unit test for OpportunityHandlers.handle_create_opportunity_manual."""
from src.api.opportunity.handler import OpportunityHandlers

class _OpportunityRepositoryStub:
    def create_opportunity_manual(self, user_id, name):
        return {'status': 'ok', 'user_id': user_id, 'name': name}

def test_handle_create_opportunity_manual():
    handler = OpportunityHandlers(opportunity_repository=_OpportunityRepositoryStub())
    result = handler.handle_create_opportunity_manual('user-3', 'Test Opportunity')
    assert result['status'] == 'ok'
    assert result['user_id'] == 'user-3'
    assert result['name'] == 'Test Opportunity'
