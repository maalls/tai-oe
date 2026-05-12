"""Email classification request handler."""

from typing import Dict
from src.repository.email_repository import EmailRepository


class ClassifyHandler:
    """Handle email classification API requests.
    
    This class acts as a controller/handler layer that delegates
    business logic to the EmailRepository.
    """

    def __init__(self):
        """Initialize classification handler."""
        self.repository = EmailRepository()

    def handle_classify(self, email_uuid: str, user_id: str, force: bool = False) -> Dict:
        """Classify an email and store the result.

        Parameters
        ----------
        email_uuid : str
            The UUID of the email to classify
        user_id : str
            The user ID (for authorization)

        Returns
        -------
        dict
            Response with status, message, and classification result
        """
        return self.repository.classify_email(email_uuid, user_id, force)
