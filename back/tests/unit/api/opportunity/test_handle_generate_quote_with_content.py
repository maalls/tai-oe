"""Unit test for OpportunityHandlers.handle_generate_quote_with_content."""
from src.api.opportunity.handler import OpportunityHandlers

class _OpportunityRepositoryStub:
    def handle_generate_quote_with_content(self, opportunity_id, content, user_id=None):
        return {'status': 'ok', 'opportunity_id': opportunity_id, 'content': content, 'user_id': user_id}

def test_handle_generate_quote_with_content():
    handler = OpportunityHandlers(opportunity_repository=_OpportunityRepositoryStub())
    result = handler.handle_generate_quote_with_content('opp-1', 'quote content', user_id='user-1')
    assert result['status'] == 'ok'
    assert result['opportunity_id'] == 'opp-1'
    assert result['content'] == 'quote content'
    assert result['user_id'] == 'user-1'
