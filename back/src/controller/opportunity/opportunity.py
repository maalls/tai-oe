
from src.supabase.supabase_client import get_supabase_service
from src.repository.opportunity import OpportunityRepository

class Opportunity:
    def __init__(self):
        self.supabase = get_supabase_service()
        self.opportunity_repository = OpportunityRepository()

