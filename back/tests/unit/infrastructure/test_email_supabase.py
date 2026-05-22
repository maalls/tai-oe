"""Tests for SupabaseEmailRepository and DTO mapping."""

from datetime import datetime, timezone

import pytest

from domain.enums import EmailStatus
from infrastructure.database.dto import EmailDTO
from infrastructure.exceptions import MappingError, NotFoundError
from infrastructure.supabase.email_supabase import SupabaseEmailRepository
from tests.fixtures.sample_data import sample_email


class _DbHandlerStub:
    def __init__(self, query_rows=None, update_rows_affected=1):
        self.query_rows = query_rows or []
        self.update_rows_affected = update_rows_affected
        self.last_update = None

    def execute_dict_query(self, _query, _params=None):
        return self.query_rows

    def execute_update(self, query, params=None):
        self.last_update = (query, params)
        return self.update_rows_affected


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
    db_handler = _DbHandlerStub(
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

    repo = SupabaseEmailRepository(db_handler=db_handler)
    email = repo.get_by_id("e-1")

    assert email.id == "e-1"
    assert email.status == EmailStatus.CLASSIFIED
    assert email.classification == "quote"
    assert email.classified_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_get_by_id_raises_not_found():
    db_handler = _DbHandlerStub([])
    repo = SupabaseEmailRepository(db_handler=db_handler)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_save_writes_transformed_sql_payload():
    db_handler = _DbHandlerStub([])
    repo = SupabaseEmailRepository(db_handler=db_handler)
    email = sample_email(id="e-save", status=EmailStatus.UNREAD)

    repo.save(email)

    assert db_handler.last_update is not None
    _, params = db_handler.last_update

    assert params[1] == email.sender
    assert params[3] is False


def test_to_domain_raises_mapping_error_on_invalid_payload():
    db_handler = _DbHandlerStub([])
    repo = SupabaseEmailRepository(db_handler=db_handler)

    with pytest.raises(MappingError):
        repo._to_domain({"id": "broken"})
