"""
Domain Enums - Synced with PostgreSQL types (back/schema/types/*.sql)
"""
from enum import Enum


class DocumentStatus(Enum):
    """Synced with: back/schema/types/document_status.sql"""
    DRAFT = "DRAFT"
    SENT = "SENT"
    RECEIVED = "RECEIVED"
    SUBMITTED = "SUBMITTED"
    SHORTLISTED = "SHORTLISTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    OVERDUE = "OVERDUE"
    DISPUTED = "DISPUTED"
    APPLIED = "APPLIED"


class InvoicePaymentStatus(Enum):
    """Synced with: back/schema/types/invoice_payment_status.sql"""
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class ContactRole(Enum):
    """Synced with: back/schema/types/contact_role.sql"""
    DECISION_MAKER = "DECISION_MAKER"
    INFLUENCER = "INFLUENCER"
    BUYER = "BUYER"
    TECHNICAL = "TECHNICAL"
    FINANCE = "FINANCE"


class DocumentType(Enum):
    """Synced with: back/schema/types/document_type.sql"""
    RFI = "RFI"
    RFQ = "RFQ"
    PROPOSAL = "PROPOSAL"
    INVOICE = "INVOICE"
    QUOTE = "QUOTE"
    RFP = "RFP"
    PO = "PO"
    CONTRACT = "CONTRACT"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    ACCEPTANCE = "ACCEPTANCE"
    CREDIT_NOTE = "CREDIT_NOTE"
    NDA = "NDA"
    DPA = "DPA"
    SLA = "SLA"
    CGV = "CGV"
    FAMILY_DISCOUNT = "FAMILY_DISCOUNT"
    ATTACHMENT = "ATTACHMENT"


class DocumentChannel(Enum):
    """Synced with: back/schema/types/document_channel.sql"""
    EMAIL = "EMAIL"
    PORTAL = "PORTAL"
    PHONE = "PHONE"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


class DocumentLinkType(Enum):
    """Synced with: back/schema/types/document_link_type.sql"""
    QUOTE_TO_PO = "QUOTE_TO_PO"
    PO_TO_INVOICE = "PO_TO_INVOICE"
    QUOTE_TO_INVOICE = "QUOTE_TO_INVOICE"
    CONTRACT_TO_SOW = "CONTRACT_TO_SOW"
    DELIVERY_TO_INVOICE = "DELIVERY_TO_INVOICE"
    ACCEPTANCE_TO_INVOICE = "ACCEPTANCE_TO_INVOICE"
    QUOTE_REVISION = "QUOTE_REVISION"


class QuoteAcceptanceMode(Enum):
    """Synced with: back/schema/types/quote_acceptance_mode.sql"""
    SIGNED_QUOTE = "SIGNED_QUOTE"
    EMAIL_OK = "EMAIL_OK"
    PORTAL_CLICK = "PORTAL_CLICK"


class UnitType(Enum):
    """Synced with: back/schema/types/unit_type.sql"""
    U = "U"
    M = "M"
    H = "H"
    PACK = "PACK"
    KG = "KG"
    L = "L"
    DAY = "DAY"


class OpportunityStage(Enum):
    """Synced with: back/schema/tables/opportunity.sql opportunity_stage"""

    NEW_LEAD = "NEW_LEAD"
    QUALIFYING = "QUALIFYING"
    NEEDS_DEFINED = "NEEDS_DEFINED"
    RFP_IN_PROGRESS = "RFP_IN_PROGRESS"
    RFQ_IN_PROGRESS = "RFQ_IN_PROGRESS"
    OFFER_SENT = "OFFER_SENT"
    NEGOTIATION = "NEGOTIATION"
    COMMITMENT = "COMMITMENT"
    PREPARATION = "PREPARATION"
    DELIVERY_IN_PROGRESS = "DELIVERY_IN_PROGRESS"
    ACCEPTED = "ACCEPTED"
    INVOICED = "INVOICED"
    PAID = "PAID"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"
    ON_HOLD = "ON_HOLD"


class OpportunityStatus(Enum):
    """Synced with: back/schema/tables/opportunity.sql opportunity_status"""

    OPEN = "OPEN"
    WON = "WON"
    LOST = "LOST"
    ON_HOLD = "ON_HOLD"


# Custom enums (not in PostgreSQL)
class EmailStatus(Enum):
    """Status of an email in the system"""
    UNREAD = "unread"
    CLASSIFIED = "classified"
    ARCHIVED = "archived"
