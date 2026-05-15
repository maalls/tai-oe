"""Unit tests for Opportunity controller quote generation delegation."""

from src.api.business.opportunity_controller import Opportunity


class _OpportunityRepositoryStub:
    def __init__(self):
        self.calls = []

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        self.calls.append((opportunity_id, user_id))
        return {"status": "ok", "opportunity_id": opportunity_id}


def test_handle_generate_quote_for_opportunity_delegates_to_repository():
    controller = Opportunity.__new__(Opportunity)
    controller.opportunity_repository = _OpportunityRepositoryStub()

    result = controller.handle_generate_quote_for_opportunity("opp-99", user_id="u-9")

    assert result == {"status": "ok", "opportunity_id": "opp-99"}
    assert controller.opportunity_repository.calls == [("opp-99", "u-9")]