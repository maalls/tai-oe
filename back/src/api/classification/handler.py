"""Email classification request handler."""

from typing import Dict

from src.service.classification.handler_service import ClassifyService


class ClassifyHandler:
    """Handle email classification API requests.
    
    This class acts as a controller/handler layer that delegates
    business logic to the EmailRepository.
    """

    def __init__(
        self,
        service_factory=None,
        repository=None,
        classify_service: ClassifyService = None,
    ):
        """Initialize classification handler."""
        # Keep backward compatible dependency injection while delegating logic.
        self.classify_service = classify_service or ClassifyService(
            service_factory=service_factory,
            repository=repository,
        )

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
        return self.classify_service.handle_classify(email_uuid=email_uuid, user_id=user_id, force=force)

