from src.repository.email_repository import EmailRepository


def test_create_opportunity_from_email_creates_opportunity(monkeypatch):
    class _EmailDbHandlerMock:
        def __init__(self):
            self.calls = []

        def get_email(self, email_id):
            self.calls.append(("get_email", email_id))
            return {
                "body_full": "Need a quote for the attached project.",
                "body_preview": "Need a quote",
                "from_email": "buyer@example.com",
                "from_name": "Buyer Co",
                "category": "RFQ",
            }

        def find_opportunity_by_source_reference(self, user_id, source_reference_id):
            self.calls.append(("find_opportunity_by_source_reference", user_id, source_reference_id))
            return None

        def create_opportunity(self, owner_user_id, account_id, name, stage, source_reference_id, source="email", status="OPEN"):
            self.calls.append(("create_opportunity", owner_user_id, account_id, name, stage, source_reference_id, source, status))
            return "opp-1"

    repo = EmailRepository()
    repo.db_handler = _EmailDbHandlerMock()
    repo.generate_account_from_email = lambda email: "account-1"
    monkeypatch.setattr("src.repository.email_repository.extract_rfp_from_text", lambda text: {"title": "Project Alpha"})

    result = repo.create_opportunity_from_email("email-1", "user-1")

    assert result == {
        "status": "ok",
        "opportunity": {
            "id": "opp-1",
            "name": "Project Alpha",
            "stage": "RFQ_IN_PROGRESS",
            "status": "OPEN",
            "account_id": "account-1",
            "message": "Opportunity created successfully from RFQ",
        },
    }
    assert repo.db_handler.calls[0] == ("get_email", "email-1")
    assert repo.db_handler.calls[1] == ("find_opportunity_by_source_reference", "user-1", "email-1")
    assert repo.db_handler.calls[2][0] == "create_opportunity"
