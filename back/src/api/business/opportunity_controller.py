
from src.supabase.supabase_client import get_supabase_service
from src.repository.opportunity import OpportunityRepository


class Opportunity:
    def __init__(self):
        self.supabase = get_supabase_service()
        self.opportunity_repository = OpportunityRepository()

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None):
        """Delegate opportunity-scoped quote generation to the current backend."""
        return self.opportunity_repository.handle_generate_quote_for_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
        )

