"""
Tests for domain enums
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
from domain.enums import (
    DocumentStatus, InvoicePaymentStatus, ContactRole,
    DocumentType, DocumentChannel, EmailStatus
)


class TestDocumentStatus:
    """Test DocumentStatus enum"""

    def test_document_status_values_exist(self):
        """Verify all document statuses have correct values"""
        assert DocumentStatus.DRAFT.value == "DRAFT"
        assert DocumentStatus.SENT.value == "SENT"
        assert DocumentStatus.PAID.value == "PAID"

    def test_document_status_can_be_created_from_value(self):
        """Verify enums can be created from values"""
        status = DocumentStatus("DRAFT")
        assert status == DocumentStatus.DRAFT


class TestInvoicePaymentStatus:
    """Test InvoicePaymentStatus enum"""

    def test_invoice_payment_status_values(self):
        """Verify payment status values"""
        assert InvoicePaymentStatus.PAID.value == "PAID"
        assert InvoicePaymentStatus.UNPAID.value == "UNPAID"


class TestEmailStatus:
    """Test EmailStatus enum"""

    def test_email_status_unread(self):
        """Verify UNREAD status"""
        assert EmailStatus.UNREAD.value == "unread"

    def test_email_status_classified(self):
        """Verify CLASSIFIED status"""
        assert EmailStatus.CLASSIFIED.value == "classified"

    def test_all_email_statuses_defined(self):
        """Verify all expected statuses exist"""
        assert hasattr(EmailStatus, "UNREAD")
        assert hasattr(EmailStatus, "CLASSIFIED")
        assert hasattr(EmailStatus, "ARCHIVED")


class TestContactRole:
    """Test ContactRole enum"""

    def test_contact_roles_exist(self):
        """Verify contact roles are defined"""
        assert ContactRole.DECISION_MAKER.value == "DECISION_MAKER"
        assert ContactRole.BUYER.value == "BUYER"
