"""
Tests for domain enums
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
from domain.enums import (
    ContactRole,
    DocumentChannel,
    DocumentLinkType,
    DocumentStatus,
    DocumentType,
    EmailStatus,
    InvoicePaymentStatus,
    OpportunityStage,
    OpportunityStatus,
    QuoteAcceptanceMode,
    UnitType,
)


class TestDocumentStatus:
    """Test DocumentStatus enum"""

    def test_document_status_values_exist(self):
        """Verify all document statuses have correct values"""
        assert [member.value for member in DocumentStatus] == [
            "DRAFT",
            "SENT",
            "RECEIVED",
            "SUBMITTED",
            "SHORTLISTED",
            "ACCEPTED",
            "REJECTED",
            "CONFIRMED",
            "FULFILLED",
            "CANCELLED",
            "EXPIRED",
            "PAID",
            "PARTIALLY_PAID",
            "OVERDUE",
            "DISPUTED",
            "APPLIED",
        ]

    def test_document_status_can_be_created_from_value(self):
        """Verify enums can be created from values"""
        status = DocumentStatus("DRAFT")
        assert status == DocumentStatus.DRAFT


class TestInvoicePaymentStatus:
    """Test InvoicePaymentStatus enum"""

    def test_invoice_payment_status_values(self):
        """Verify payment status values"""
        assert [member.value for member in InvoicePaymentStatus] == [
            "UNPAID",
            "PARTIAL",
            "PAID",
            "CANCELLED",
        ]


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


class TestDocumentType:
    """Test DocumentType enum"""

    def test_document_type_values(self):
        assert [member.value for member in DocumentType] == [
            "RFI",
            "RFQ",
            "PROPOSAL",
            "INVOICE",
            "QUOTE",
            "RFP",
            "PO",
            "CONTRACT",
            "DELIVERY_NOTE",
            "ACCEPTANCE",
            "CREDIT_NOTE",
            "NDA",
            "DPA",
            "SLA",
            "CGV",
            "FAMILY_DISCOUNT",
            "ATTACHMENT",
        ]


class TestDocumentChannel:
    """Test DocumentChannel enum"""

    def test_document_channel_values(self):
        assert [member.value for member in DocumentChannel] == [
            "EMAIL",
            "PORTAL",
            "PHONE",
            "MANUAL",
            "OTHER",
        ]


class TestDocumentLinkType:
    """Test DocumentLinkType enum"""

    def test_document_link_type_values(self):
        assert [member.value for member in DocumentLinkType] == [
            "QUOTE_TO_PO",
            "PO_TO_INVOICE",
            "QUOTE_TO_INVOICE",
            "CONTRACT_TO_SOW",
            "DELIVERY_TO_INVOICE",
            "ACCEPTANCE_TO_INVOICE",
            "QUOTE_REVISION",
        ]


class TestQuoteAcceptanceMode:
    """Test QuoteAcceptanceMode enum"""

    def test_quote_acceptance_mode_values(self):
        assert [member.value for member in QuoteAcceptanceMode] == [
            "SIGNED_QUOTE",
            "EMAIL_OK",
            "PORTAL_CLICK",
        ]


class TestUnitType:
    """Test UnitType enum"""

    def test_unit_type_values(self):
        assert [member.value for member in UnitType] == [
            "U",
            "M",
            "H",
            "PACK",
            "KG",
            "L",
            "DAY",
        ]


class TestOpportunityEnums:
    """Test opportunity enums"""

    def test_opportunity_stage_values(self):
        assert [member.value for member in OpportunityStage] == [
            "NEW_LEAD",
            "QUALIFYING",
            "NEEDS_DEFINED",
            "RFP_IN_PROGRESS",
            "RFQ_IN_PROGRESS",
            "OFFER_SENT",
            "NEGOTIATION",
            "COMMITMENT",
            "PREPARATION",
            "DELIVERY_IN_PROGRESS",
            "ACCEPTED",
            "INVOICED",
            "PAID",
            "CLOSED_WON",
            "CLOSED_LOST",
            "ON_HOLD",
        ]

    def test_opportunity_status_values(self):
        assert [member.value for member in OpportunityStatus] == [
            "OPEN",
            "WON",
            "LOST",
            "ON_HOLD",
        ]


class TestContactRole:
    """Test ContactRole enum"""

    def test_contact_roles_exist(self):
        """Verify contact roles are defined"""
        assert ContactRole.DECISION_MAKER.value == "DECISION_MAKER"
        assert ContactRole.BUYER.value == "BUYER"
