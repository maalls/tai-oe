# LLM-Based Contact Extraction from Email

## Overview

Implemented a feature to extract contact and account information from email bodies using an LLM (Large Language Model), allowing users to automatically discover contact details from email content with a single click.

## Components Implemented

### 1. Frontend (MailItemExpanded.vue)

**File**: `/Users/malo/Documents/Projects/rkllm-server/external/rag/front/src/components/mail/MailItemExpanded.vue`

**Features**:

- Added "Extract Contact" button next to the Email Body header
- Button displays loading state "Extracting..." during API call
- On success, shows alert with extracted contact and account details:
  - Contact: Name, Email, Phone, Title
  - Account: Name, Industry, Country
- Clean error handling with user-friendly error messages

**Code**:

- `isExtractingContact` ref for managing loading state
- `extractContactFromBody()` async function that:
  - POSTs to `/api/email/extract-contact` with email_id and email_body
  - Parses JSON response
  - Displays extracted information in alert

### 2. Backend Endpoints and Routing

**File**: `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/rag.py`

**Endpoint**: `POST /api/email/extract-contact`

- Accepts JSON payload with `email_id` and `email_body`
- Delegates to handlers.handle_extract_contact_from_email()
- Returns JSON response with status, contact, and account information

### 3. Handler Chain

**File**: `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/handlers.py`

- `handle_extract_contact_from_email()` method that delegates to EmailHandlers

**File**: `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/email_handler.py`

- `handle_extract_contact_from_email()` method that delegates to EmailRepository

### 4. Repository Implementation

**File**: `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/repository/email_repository.py`

**Method**: `extract_contact_from_email_body(email_id, email_body)`

**Functionality**:

1. Validates email_body parameter
2. Initializes LLMClient via LLMClientFactory
3. Creates structured prompt asking LLM to extract:
   - Contact: name, email, phone, title
   - Account: name, industry, country
4. Calls LLM using `ask_json()` method
5. Parses JSON response
6. Returns structured response with extracted data

**Key Features**:

- Temperature set to 0.3 for consistent extraction
- Max tokens set to 500 to keep response focused
- Robust JSON parsing with fallback error handling
- Comprehensive exception handling with logging

### 5. LLM Configuration

Uses existing LLMClientFactory pattern:

- Default model: `qwen/qwen2.5-vl-7b`
- Default endpoint: `http://192.168.1.5:1234/v1`
- Can be overridden via environment variables or config.yml

## Response Format

### Success Response

```json
{
  "status": "ok",
  "contact": {
    "name": "John Smith",
    "email": "john.smith@acme.com",
    "phone": "555-0123",
    "title": "VP of Sales"
  },
  "account": {
    "name": "Acme Corporation",
    "industry": "Technology",
    "country": "USA"
  },
  "message": "Contact information extracted successfully"
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error description"
}
```

## Testing

Created comprehensive test script: `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/test_llm_extraction.py`

**Sample Email**:

```
Hi there,

I'm John Smith, the VP of Sales at Acme Corporation. We're interested in learning more about your services.

Please feel free to reach out to me at john.smith@acme.com or call me at 555-0123.

Best regards,
John Smith
VP of Sales
Acme Corporation
San Francisco, CA
```

**Test Results**: ✓ PASSED

- Successfully extracted all contact and account information
- LLM correctly parsed unstructured email text
- JSON response properly formatted and parsed

## Usage Workflow

1. User opens email in MailItemExpanded component
2. Email body is loaded and displayed
3. User clicks "Extract Contact" button
4. Frontend sends POST request to backend with email body
5. Backend calls LLM to extract structured information
6. Response is returned and displayed in alert to user
7. User can then manually create contact record if desired

## Future Enhancements

Potential improvements for future iterations:

1. Auto-create contact and account records in database
2. Link extracted contact to current opportunity
3. Show extracted data in modal instead of alert for better UX
4. Handle multiple contacts in single email
5. Validate extracted email addresses and phone numbers
6. Cache extraction results per email to avoid duplicate API calls
7. Add role/title mapping to contact_role enum (DECISION_MAKER, INFLUENCER, BUYER, etc.)

## Dependencies

- `src.controller.llm_factory.LLMClientFactory`: LLM client initialization
- `src.llm.client.LLMClient`: OpenAI-compatible chat completions client
- Standard libraries: json, re, traceback

## Files Modified

1. `/Users/malo/Documents/Projects/rkllm-server/external/rag/front/src/components/mail/MailItemExpanded.vue`
   - Added extract contact button and handler function

2. `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/rag.py`
   - Added POST endpoint for `/api/email/extract-contact`

3. `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/handlers.py`
   - Added delegation method for extract contact

4. `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/email_handler.py`
   - Added delegation method for extract contact

5. `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/repository/email_repository.py`
   - Implemented `extract_contact_from_email_body()` method

## Testing Status

✓ LLM extraction works correctly
✓ Frontend button and handler functional
✓ Backend endpoint and routing established
✓ Response parsing successful
✓ Error handling implemented
