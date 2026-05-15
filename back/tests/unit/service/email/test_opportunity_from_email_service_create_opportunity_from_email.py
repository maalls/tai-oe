"""Tests for OpportunityFromEmailService.create_opportunity_from_email."""

from service.email.opportunity_from_email_service import OpportunityFromEmailService


def test_create_opportunity_from_email_triggers_quote_generation_on_success():
    calls = []

    def _create(message_id: str, user_id: str = None):
        calls.append(("create", message_id, user_id))
        return {"status": "ok", "opportunity": {"id": "opp-1"}}

    def _generate(opportunity_id: str, user_id: str = None):
        calls.append(("generate", opportunity_id, user_id))
        return {"status": "ok"}

    service = OpportunityFromEmailService(
        create_opportunity_from_email=_create,
        generate_quote_for_opportunity=_generate,
    )

    result = service.create_opportunity_from_email("email-1", user_id="u-1")

    assert result == {"status": "ok", "opportunity": {"id": "opp-1"}}
    assert calls == [
        ("create", "email-1", "u-1"),
        ("generate", "opp-1", "u-1"),
    ]


def test_create_opportunity_from_email_skips_quote_generation_on_error():
    calls = []

    def _create(message_id: str, user_id: str = None):
        calls.append(("create", message_id, user_id))
        return {"status": "error", "message": "boom"}

    def _generate(opportunity_id: str, user_id: str = None):
        calls.append(("generate", opportunity_id, user_id))
        return {"status": "ok"}

    service = OpportunityFromEmailService(
        create_opportunity_from_email=_create,
        generate_quote_for_opportunity=_generate,
    )

    result = service.create_opportunity_from_email("email-2", user_id="u-2")

    assert result == {"status": "error", "message": "boom"}
    assert calls == [("create", "email-2", "u-2")]
