# Send Invoice Implementation

## Overview

Complete implementation of invoice sending functionality allowing users to email invoices with PDF attachments to customers.

## Backend Implementation

### API Endpoint

- **Route**: `POST /api/invoice/{id}/send`
- **Location**: [back/src/controller/rag.py](back/src/controller/rag.py)
- **Authentication**: Requires Bearer token

### Request Payload

```json
{
  "to": ["recipient@example.com"],
  "cc": ["cc@example.com"],
  "subject": "Invoice #INV-001",
  "body": "Please find attached your invoice."
}
```

### Business Handler

- **Method**: `handle_send_invoice()`
- **Location**: [back/src/controller/business_handler.py](back/src/controller/business_handler.py)
- **Flow**:
  1. Validates invoice exists and is type INVOICE
  2. Checks PDF has been generated (storage_key exists)
  3. Validates email payload (at least one "to" address required)
  4. Retrieves PDF from storage (invoice/ or assets/ directory)
  5. Sends email via EmailHandlers with PDF attachment
  6. Updates invoice status to "SENT" on success
  7. Returns status with message_id

### Email Integration

- Uses existing `EmailHandlers.handle_send_email_with_attachments()`
- Supports multiple recipients (to and cc)
- Attaches invoice PDF from storage

## Frontend Implementation

### Invoice Detail Page

- **Component**: [front/src/components/opportunity/InvoiceDetailPage.vue](front/src/components/opportunity/InvoiceDetailPage.vue)
- **Features**:
  - "Send" button opens email composition modal
  - Auto-fills recipient email from opportunity → account → contact
  - Default subject: "Invoice {external_ref}"
  - Default body with invoice details
  - Validates PDF exists before allowing send
  - Shows success/error messages
  - Reloads invoice after send to show updated SENT status

### Email Composition Modal

- **Fields**:
  - To (required): Comma-separated email addresses
  - CC (optional): Comma-separated email addresses
  - Subject (required): Email subject line
  - Message (required): Email body text
- **Attachment**: Automatically includes invoice PDF
- **Validation**: Requires at least one recipient

### Invoices List Page

- **Component**: [front/src/components/opportunity/InvoicesPage.vue](front/src/components/opportunity/InvoicesPage.vue)
- **Feature**: "Send" button navigates to invoice detail page

### Pipeline Stage (Accepted)

- **Component**: [front/src/components/opportunity/pipeline/PipelineStageAccepted.vue](front/src/components/opportunity/pipeline/PipelineStageAccepted.vue)
- **Feature**: "Send invoice" button navigates to invoices page

## User Flow

1. User generates invoice from quote (ACCEPTED stage or via API)
2. Invoice PDF is automatically generated
3. User clicks "Send" button (from detail page, list, or pipeline)
4. Modal opens with pre-filled email details
5. User can edit recipient, subject, body
6. User clicks "Send Invoice"
7. Backend validates and sends email with PDF attachment
8. Invoice status updates to "SENT"
9. Success message displayed

## Status Tracking

- **DRAFT**: Invoice created but not sent
- **SENT**: Invoice sent via email
- **PAID**: Invoice payment received (future enhancement)

## Testing

### Manual Testing Steps

1. Create an invoice from a quote
2. Verify PDF is generated automatically
3. Navigate to invoice detail page
4. Click "Send" button
5. Verify modal opens with pre-filled data
6. Enter recipient email(s)
7. Submit form
8. Verify email is sent
9. Verify invoice status changes to "SENT"

### Test Invoice Send API

```bash
# Get auth token first
TOKEN="your-bearer-token"

# Send invoice
curl -X POST http://localhost:8088/api/invoice/{invoice-id}/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["customer@example.com"],
    "cc": ["accounting@company.com"],
    "subject": "Invoice #INV-001",
    "body": "Please find attached your invoice.\n\nThank you for your business."
  }'
```

## Files Modified

### Backend

1. [back/src/controller/business_handler.py](back/src/controller/business_handler.py)
   - Added `handle_send_invoice()` method (93 lines)
   - Validates invoice and PDF
   - Sends email with attachment
   - Updates status to SENT

2. [back/src/controller/handlers.py](back/src/controller/handlers.py)
   - Added `handle_send_invoice()` wrapper method

3. [back/src/controller/rag.py](back/src/controller/rag.py)
   - Added POST `/api/invoice/{id}/send` endpoint
   - Parses JSON payload
   - Requires authentication

### Frontend

1. [front/src/components/opportunity/InvoiceDetailPage.vue](front/src/components/opportunity/InvoiceDetailPage.vue)
   - Added send invoice modal UI
   - Added email form state
   - Implemented `sendInvoice()` function
   - Auto-fills recipient email
   - Shows success/error feedback

2. [front/src/components/opportunity/InvoicesPage.vue](front/src/components/opportunity/InvoicesPage.vue)
   - Updated "Send" button to navigate to detail page

3. [front/src/components/opportunity/pipeline/PipelineStageAccepted.vue](front/src/components/opportunity/pipeline/PipelineStageAccepted.vue)
   - Updated "Send invoice" button to navigate to invoices page

## Dependencies

- EmailHandlers (for email sending)
- WeasyPrint (for PDF generation - already used)
- Supabase (for database operations)
- SMTP/SendGrid configuration (for actual email delivery)

## Future Enhancements

1. Email template customization
2. Invoice resend functionality
3. Email delivery tracking
4. Payment recording (mark as PAID)
5. Invoice editing (before SENT status)
6. Email history/logs
7. Scheduled invoice sending
8. Recurring invoices
