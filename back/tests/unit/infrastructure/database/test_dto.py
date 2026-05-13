"""Tests for DTO SQL mapping helpers."""

from datetime import date, datetime, timezone

from src.infrastructure.database.dto import EmailDTO, OpportunityDTO, RfpDTO


def test_email_dto_ignores_extra_fields():
    dto = EmailDTO(
        id="e-1",
        from_email="test@example.com",
        is_classified=False,
        unknown_field="ignored",
    )

    assert dto.id == "e-1"
    assert dto.from_email == "test@example.com"


def test_opportunity_dto_parses_date_and_ignores_extra_fields():
    dto = OpportunityDTO(
        id="o-1",
        account_id="a-1",
        name="Deal",
        stage="NEGOTIATION",
        status="OPEN",
        expected_close_date="2026-06-01",
        created_at="2026-05-13T10:20:30Z",
        extra_field="ignored",
    )

    assert dto.expected_close_date == date(2026, 6, 1)
    assert dto.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_rfp_dto_parses_datetime_and_ignores_extra_fields():
    dto = RfpDTO(
        id="r-1",
        type="RFP",
        title="RFP A",
        status="DRAFT",
        created_at="2026-05-13T10:20:30Z",
        extra_field="ignored",
    )

    assert dto.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)
