"""Compatibility facade for legacy POST route handlers.

Implementation is now organized in domain handler modules under src.api.*.handler.
This module keeps stable imports for server wiring.
"""

from src.api.action.handler import (
    handle_action_execute_post,
    handle_action_pause_post,
    handle_action_resume_post,
    handle_actions_create_post,
)
from src.api.auth.handler import (
    handle_auth_login_post,
    handle_auth_logout_post,
    handle_auth_signup_post,
)
from src.api.csv.handler import handle_csv_source_post
from src.api.document.handler import (
    handle_chat_attachments_post,
    handle_document_extract_rfp_post,
    handle_document_update_content_post,
)
from src.api.email.handler import (
    handle_email_auth_status_post,
    handle_email_extract_contact_post,
    handle_email_resync_post,
    handle_email_senders_high_risk_post,
    handle_email_senders_verified_post,
    handle_emails_classify_post,
    handle_imap_config_post,
    handle_imap_test_post,
)
from src.api.entity.handler import handle_entity_update_post
from src.api.file.handler import (
    handle_curl_post,
    handle_fs_create_post,
    handle_fs_read_post,
)
from src.api.invoice.handler import (
    handle_invoice_pdf_post,
    handle_invoice_send_post,
    handle_quote_invoice_post,
)
from src.api.opportunity.handler import (
    handle_opportunities_create_from_email_post,
    handle_opportunities_create_from_rfp_post,
    handle_opportunities_create_manual_post,
    handle_opportunity_rfq_create_from_text_post,
    handle_opportunity_rfq_generate_post,
    handle_send_quote_for_opportunity_post,
)
from src.api.product.handler import handle_products_post
from src.api.quote.handler import (
    handle_quote_pdf_post,
    handle_quote_send_post,
    handle_quote_submit_post,
    handle_quote_update_post,
)
from src.api.rfq.handler import (
    handle_rfp_post,
    handle_rfq_generate_post,
)

__all__ = [
    "handle_action_execute_post",
    "handle_action_pause_post",
    "handle_action_resume_post",
    "handle_actions_create_post",
    "handle_auth_login_post",
    "handle_auth_logout_post",
    "handle_auth_signup_post",
    "handle_chat_attachments_post",
    "handle_csv_source_post",
    "handle_curl_post",
    "handle_document_extract_rfp_post",
    "handle_document_update_content_post",
    "handle_email_auth_status_post",
    "handle_email_extract_contact_post",
    "handle_email_resync_post",
    "handle_email_senders_high_risk_post",
    "handle_email_senders_verified_post",
    "handle_emails_classify_post",
    "handle_entity_update_post",
    "handle_fs_create_post",
    "handle_fs_read_post",
    "handle_imap_config_post",
    "handle_imap_test_post",
    "handle_invoice_pdf_post",
    "handle_invoice_send_post",
    "handle_opportunities_create_from_email_post",
    "handle_opportunities_create_from_rfp_post",
    "handle_opportunities_create_manual_post",
    "handle_opportunity_rfq_create_from_text_post",
    "handle_opportunity_rfq_generate_post",
    "handle_products_post",
    "handle_quote_invoice_post",
    "handle_quote_pdf_post",
    "handle_quote_send_post",
    "handle_quote_submit_post",
    "handle_quote_update_post",
    "handle_rfp_post",
    "handle_rfq_generate_post",
    "handle_send_quote_for_opportunity_post",
]
