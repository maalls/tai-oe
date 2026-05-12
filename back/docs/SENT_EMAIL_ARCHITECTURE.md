# Sent Email Architecture

## Design Decision

Created a dedicated `sent_email` table to track outbound emails separately from the existing `email` table.

### Why Separate Tables?

**`email` table (inbound):**

- Stores emails fetched from Gmail/Outlook
- Used for lead generation and RFP detection
- Tracks email classification (RFP, RFQ, Quote, etc.)
- Links to contacts/accounts for lead management

**`sent_email` table (outbound):**

- Stores emails sent by the system
- Tracks invoice sends, quote sends, etc.
- Monitors delivery status and engagement
- Links to documents (invoices, quotes)

### Benefits

1. **Clean Separation**: Inbound vs outbound emails have different purposes and schemas
2. **Multiple Sends**: Can track multiple sends per document (resends, reminders)
3. **Delivery Tracking**: Store Gmail message_id for tracking delivery, opens, bounces
4. **Future Features**: Read receipts, bounce tracking, email analytics
5. **Query Performance**: Optimized indexes for sent email queries

## Database Schema

```sql
CREATE TABLE sent_email (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES document(id),  -- Invoice, quote, etc.
  opportunity_id UUID REFERENCES opportunity(id),

  -- Email details
  from_email TEXT NOT NULL,
  to_emails TEXT[] NOT NULL,     -- Array for multiple recipients
  cc_emails TEXT[],
  bcc_emails TEXT[],
  subject TEXT NOT NULL,
  body TEXT NOT NULL,

  -- Provider tracking
  provider TEXT DEFAULT 'gmail',
  provider_message_id TEXT,      -- Gmail message ID
  provider_metadata JSONB,       -- Provider-specific data

  -- Delivery tracking
  status TEXT DEFAULT 'sent',    -- sent, delivered, opened, bounced, failed
  sent_at TIMESTAMP,
  delivered_at TIMESTAMP,
  opened_at TIMESTAMP,
  bounced_at TIMESTAMP,
  error_message TEXT,

  -- Metadata
  attachment_names TEXT[],
  sent_by_user_id UUID,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

## API Flow

### Send Invoice (POST /api/invoice/{id}/send)

1. **Validate**: Check invoice exists and has PDF
2. **Send Email**: Via GmailClient.send_email_with_attachment()
3. **Update Document**: Set invoice.status = 'SENT'
4. **Save Sent Email**: Insert record into sent_email table
   - Store to/cc/subject/body
   - Save Gmail message_id
   - Link to document_id and opportunity_id
5. **Return**: Success response with message_id

### Load Invoice Detail Page

1. **Load Invoice**: Fetch from document table
2. **Check Status**: If status === 'SENT'
3. **Load Sent Email**: Query sent_email table
   ```sql
   SELECT * FROM sent_email
   WHERE document_id = {invoice_id}
   ORDER BY sent_at DESC
   LIMIT 1
   ```
4. **Display**: Show read-only email view with sent data

## Frontend Implementation

### InvoiceDetailPage.vue

**State:**

```typescript
const sentEmail = ref<any>(null); // Sent email record from DB
```

**Load sent email data:**

```typescript
if (invoice.status === 'SENT') {
  const { data: sentEmailData } = await supabase
    .from('sent_email')
    .select('*')
    .eq('document_id', invoiceId)
    .order('sent_at', { ascending: false })
    .limit(1)
    .single();

  sentEmail.value = sentEmailData;
  emailForm.value = {
    to: sentEmailData.to_emails.join(', '),
    cc: sentEmailData.cc_emails.join(', '),
    subject: sentEmailData.subject,
    body: sentEmailData.body,
  };
}
```

**Conditional UI:**

```vue
<!-- Sent Email View -->
<div v-if="invoice?.status === 'SENT'">
  <h3>Invoice Sent ✓</h3>
  <div>From: {{ sentEmail.from_email }}</div>
  <div>To: {{ emailForm.to }}</div>
  <div>CC: {{ emailForm.cc }}</div>
  <div>Subject: {{ emailForm.subject }}</div>
  <div>Message: {{ emailForm.body }}</div>
  <div>Sent: {{ formatDate(sentEmail.sent_at) }}</div>
</div>

<!-- Send Form -->
<div v-else>
  <form @submit="submitSendInvoice">...</form>
</div>
```

## Future Enhancements

1. **Delivery Tracking**
   - Poll Gmail API for delivery status
   - Update sent_email.status (delivered, opened, bounced)
   - Show status badges in UI

2. **Resend Functionality**
   - Add "Resend Invoice" button
   - Create new sent_email record
   - Track send history (all sends for one document)

3. **Email Templates**
   - Store templates in database
   - Variables: {invoice_number}, {amount}, {customer_name}
   - Support HTML email bodies

4. **Batch Sending**
   - Send multiple invoices at once
   - Queue system for rate limiting
   - Progress tracking

5. **Analytics**
   - Track open rates, delivery rates
   - A/B test email subject lines
   - Customer engagement metrics

## Migration

Run migration to create table:

```bash
cd back
python run_migration.py migrations/010_create_sent_email_table.sql
```

## Files Modified

- `back/migrations/010_create_sent_email_table.sql` - Table schema
- `back/src/controller/business_handler.py` - Save sent email after send
- `front/src/components/opportunity/InvoiceDetailPage.vue` - Load and display sent email
