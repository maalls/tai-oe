"""Service orchestrating opportunity creation from email and quote generation."""

from typing import Callable, Dict


class OpportunityFromEmailService:
    """Compose email opportunity creation and quote generation flows."""

    def __init__(
        self,
        create_opportunity_from_email: Callable[[str, str | None], Dict],
        generate_quote_for_opportunity: Callable[[str, str | None], Dict],
    ):
        self._create_opportunity_from_email = create_opportunity_from_email
        self._generate_quote_for_opportunity = generate_quote_for_opportunity

    def create_opportunity_from_email(self, message_id: str, user_id: str = None) -> Dict:
        """Create opportunity from email and trigger quote generation when creation succeeds."""
        result = self._create_opportunity_from_email(message_id, user_id)
        if result.get("status") == "ok":
            opportunity = result.get("opportunity", {})
            opportunity_id = opportunity.get("id")
            if opportunity_id:
                print(f"[BusinessHandlers] Generating quote for opportunity {opportunity_id} by user")
                self._generate_quote_for_opportunity(opportunity_id, user_id)

        return result
