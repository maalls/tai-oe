"""Tests for SupabaseEmailRepository and DTO mapping."""

from unittest.mock import MagicMock

from datetime import datetime, timezone

import pytest

from domain.enums import EmailStatus
from infrastructure.database.dto import EmailDTO
from infrastructure.exceptions import MappingError, NotFoundError
from infrastructure.supabase.email_supabase import SupabaseEmailRepository
from tests.fixtures.sample_data import sample_email


def _mock_supabase_with_data(data):
    supabase = MagicMock()
    query = supabase.table.return_value
    query.select.return_value = query
    query.eq.return_value = query
    query.limit.return_value = query
    query.order.return_value = query
    query.execute.return_value = MagicMock(data=data)
    return supabase


def test_email_dto_ignores_extra_fields():
    dto = EmailDTO(
        id="e-1",
        from_email="test@example.com",
        is_classified=False,
        unknown_field="ignored",
    )
    assert dto.id == "e-1"
    assert dto.from_email == "test@example.com"


def test_get_by_id_maps_to_domain_entity():
    supabase = _mock_supabase_with_data(
        [
            {
                "id": "e-1",
                "subject": "Need a quote",
                "from_email": "buyer@example.com",
                "body_full": "Please share pricing",
                "is_classified": True,
                "category": "quote",
                "classified_at": "2026-05-13T10:20:30Z",
            }
        ]
    )

    repo = SupabaseEmailRepository(supabase)
    email = repo.get_by_id("e-1")

    assert email.id == "e-1"
    assert email.status == EmailStatus.CLASSIFIED
    assert email.classification == "quote"
    assert email.classified_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_get_by_id_raises_not_found():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseEmailRepository(supabase)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_save_writes_transformed_sql_payload():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseEmailRepository(supabase)
    email = sample_email(id="e-save", status=EmailStatus.UNREAD)

    repo.save(email)

    update_call = supabase.table.return_value.update.call_args
    payload = update_call.args[0]

    assert payload["from_email"] == email.sender
    assert payload["is_classified"] is False


def test_to_domain_raises_mapping_error_on_invalid_payload():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseEmailRepository(supabase)

    with pytest.raises(MappingError):
        repo._to_domain({"id": "broken"})
