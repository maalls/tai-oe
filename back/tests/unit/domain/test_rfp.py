"""Tests for Rfp domain entity."""

from datetime import datetime, timezone

import pytest

from domain.enums import DocumentStatus
from domain.rfp import Rfp


def test_mark_submitted_updates_status_immutably():
    created_at = datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)
    rfp = Rfp(
        id="r-1",
        title="Need pricing",
        requester_email="buyer@example.com",
        content="Please quote",
        status=DocumentStatus.DRAFT,
        created_at=created_at,
    )

    submitted = rfp.mark_submitted()

    assert submitted.status == DocumentStatus.SUBMITTED
    assert rfp.status == DocumentStatus.DRAFT
    assert submitted.created_at == created_at
    assert rfp.created_at == created_at


def test_mark_submitted_raises_if_already_submitted():
    rfp = Rfp(
        id="r-2",
        title="Already done",
        requester_email=None,
        content=None,
        status=DocumentStatus.SUBMITTED,
    )

    with pytest.raises(ValueError):
        rfp.mark_submitted()


def test_rfp_creation_preserves_optional_fields():
    created_at = datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)
    rfp = Rfp(
        id="r-3",
        title="Full RFP",
        requester_email="buyer@example.com",
        content="Some content",
        status=DocumentStatus.DRAFT,
        created_at=created_at,
    )

    assert rfp.requester_email == "buyer@example.com"
    assert rfp.content == "Some content"
    assert rfp.created_at == created_at
