# Email Fetch Flow Comparison

## Overview

This document compares the two main email fetching flows and identifies opportunities for code reuse.

## Flow 1: API Endpoint `/api/gmail/messages?force=true`

### Entry Point

- **HTTP Route**: `GET /api/gmail/messages?force=true&max_results=50`
- **Handler**: `src/controller/handlers.py` → `handle_gmail_list_messages()`
- **Delegate**: `src/controller/email_handler.py` → `EmailHandlers.handle_gmail_list_messages()`

### Flow Steps

```
1. EmailHandlers.handle_gmail_list_messages(force=True)
   └─> EmailRepository.fetch_emails(force=True, classify=True)

2. EmailRepository.fetch_emails()
   ├─> If force=True & classify=True:
   │   └─> fetch_and_process_emails()  ← FULL WORKFLOW
   │       ├─> fetch_from_gmail_and_save()
   │       ├─> classify_unclassified_emails()
   │       └─> link_emails_to_contacts_and_accounts()
   │
   ├─> If force=True & classify=False:
   │   └─> fetch_from_gmail_and_save()  ← FETCH ONLY
   │
   └─> If force=False:
       └─> Skip fetching, use cached DB results

3. Return cached emails from database via _get_user_emails()
```

### Key Characteristics

- **Default behavior**: `force=True` triggers full fetch + classify + link
- **Date filtering**: Uses cached DB results, no explicit after-date handling
- **Classification**: Always runs `classify_unclassified_emails()` after fetch
- **Contact linking**: Automatically links emails to contacts/accounts
- **Auto-actions**: Creates opportunities + quotes for RFQ emails during classification
- **Response**: Returns emails from database with processing summary

## Flow 2: Command Line `src/command/fetch_emails.py`

### Entry Point

- **Command**: `python src/command/fetch_emails.py --user-id <ID> --max-results 50 --after-date <DATE>`
- **Main Function**: `run()`

### Flow Steps

```
1. Command Line Arguments
   ├─> --user-id: Required user ID
   ├─> --max-results: Default 50
   ├─> --classify-limit: Default 200
   └─> --after-date: Optional (auto-resolved to latest email timestamp + 1)

2. _resolve_after_date()
   ├─> If provided: use it
   ├─> If not: query latest email from database
   │   ├─> If found: use timestamp + 1 second
   │   └─> If not found: fallback to yesterday

3. run(user_id, max_results, classify_limit, after_date)
   ├─> EmailRepository.fetch_from_gmail_and_save(before_date=after_date)
   │   └─> Fetches emails with date filter
   │
   └─> EmailRepository.classify_unclassified_emails(limit=classify_limit)
       └─> Classifies pending emails

4. Exit with status code
```

### Key Characteristics

- **Date handling**: Smart default to latest email timestamp + 1 second
- **Explicit flow**: Directly calls `fetch_from_gmail_and_save()` + `classify_unclassified_emails()`
- **No auto-linking**: Does NOT call `link_emails_to_contacts_and_accounts()`
- **No processing summary**: Just prints status, no structured response
- **Exit code**: Returns 0 or 1 for success/failure

## Key Differences

| Aspect                | API Flow                         | Command Flow                                    |
| --------------------- | -------------------------------- | ----------------------------------------------- |
| **Entry point**       | HTTP endpoint                    | CLI script                                      |
| **Date filtering**    | No explicit after-date           | Smart after-date resolution                     |
| **Classify behavior** | Via `fetch_and_process_emails()` | Direct call to `classify_unclassified_emails()` |
| **Contact linking**   | YES (automatic)                  | NO                                              |
| **Auto RFQ actions**  | YES (via classify)               | YES (via classify)                              |
| **Response format**   | JSON with processing summary     | Print statements + exit code                    |
| **Error handling**    | Returns error dict               | Catches & prints, returns exit code             |

## Code Duplication Analysis

### ✅ Already Shared

1. **`EmailRepository.fetch_from_gmail_and_save()`**
   - Both flows use this to fetch from Gmail API
   - Handles pagination, last_fetched_email_id, date filtering

2. **`EmailRepository.classify_unclassified_emails()`**
   - Both flows use this to classify pending emails
   - Handles RFQ auto-actions

### ⚠️ Duplicated Logic

1. **After-date resolution**
   - **Command**: `_resolve_after_date()` in `fetch_emails.py`
   - **API**: No equivalent - always uses cached results
   - **Issue**: Command has smart logic to avoid re-fetching same emails
   - **Recommendation**: Move `_resolve_after_date()` to `EmailRepository`

2. **Fetch + Classify orchestration**
   - **Command**: Manual calls in `run()`

   ```python
   fetch_result = repo.fetch_from_gmail_and_save(...)
   classify_result = repo.classify_unclassified_emails(...)
   ```

   - **API**: Uses `fetch_and_process_emails()` wrapper

   ```python
   processing_summary = self.fetch_and_process_emails(user_id, max_results)
   ```

   - **Issue**: Two different ways to do the same thing
   - **Recommendation**: Command should use `fetch_and_process_emails()`

3. **Error handling & logging**
   - **Command**: Try/except with print statements
   - **API**: Returns error dicts, structured logging
   - **Issue**: Inconsistent error reporting
   - **Recommendation**: Standardize on structured logging

## Refactoring Recommendations

### Option 1: Make Command Use API Flow (Recommended)

**Goal**: Command script should be a thin wrapper around the repository method.

#### Changes to `src/command/fetch_emails.py`:

```python
def run(user_id: str, max_results: int = 50, classify_limit: int = 200, after_date: str = None) -> int:
    """Fetch directly from Gmail API (no cache) then classify unclassified emails."""
    repo = EmailRepository()

    try:
        # Option A: Use the full workflow method
        result = repo.fetch_and_process_emails(
            user_id=user_id,
            max_results=max_results,
            classify_limit=classify_limit
        )

        # Print summary
        print(f"[fetch-emails] Status: {result.get('status')}")
        print(f"[fetch-emails] Emails fetched: {result.get('emails_fetched', 0)}")
        print(f"[fetch-emails] Emails classified: {result.get('emails_classified', 0)}")
        print(f"[fetch-emails] Contacts created: {result.get('contacts_created', 0)}")
        print(f"[fetch-emails] Accounts created: {result.get('accounts_created', 0)}")

        return 0 if result.get('status') == 'ok' else 1

    except Exception as exc:
        print(f"[fetch-emails] Failed: {exc}")
        import traceback
        traceback.print_exc()
        return 1
```

**Pros**:

- ✅ Eliminates duplication
- ✅ Uses battle-tested API flow
- ✅ Gets contact linking automatically
- ✅ Single source of truth

**Cons**:

- ❌ Loses explicit after-date control (uses last_fetched_email_id)
- ❌ Less flexibility for custom workflows

### Option 2: Move Smart Date Logic to Repository

**Goal**: Make `after_date` resolution available to both flows.

#### Changes to `src/repository/email_repository.py`:

```python
def _resolve_after_date(self, user_id: str, provided_after_date: str | None) -> str | None:
    """Resolve after-date for Gmail query, defaulting to latest email + 1 second."""
    if provided_after_date:
        return provided_after_date

    latest = self.db_handler.get_emails_by_user(user_id, limit=1)
    if latest:
        email_date = latest[0].get("email_date")
        if email_date:
            try:
                from datetime import datetime, timezone
                from email.utils import parsedate_to_datetime

                # Parse email date
                try:
                    parsed = datetime.fromisoformat(email_date)
                except Exception:
                    parsed = parsedate_to_datetime(email_date)

                # Convert to epoch seconds + 1
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return str(int(parsed.timestamp()) + 1)
            except Exception:
                pass

    # Fallback to yesterday
    from datetime import datetime, timedelta, timezone
    fallback = datetime.now(timezone.utc) - timedelta(days=1)
    return str(int(fallback.timestamp()))

def fetch_from_gmail_and_save(
    self,
    user_id: str,
    max_results: int = 20,
    before_date: str = None,
    auto_resolve_date: bool = False
) -> Dict:
    """Fetch emails from Gmail and save to database.

    Parameters
    ----------
    auto_resolve_date : bool
        If True and before_date is None, automatically resolve to latest email + 1 second
    """
    if auto_resolve_date and not before_date:
        before_date = self._resolve_after_date(user_id, before_date)
        print(f"[EmailRepository] Auto-resolved after-date: {before_date}")

    # ... rest of existing logic
```

#### Changes to `src/command/fetch_emails.py`:

```python
def run(user_id: str, max_results: int = 50, classify_limit: int = 200, after_date: str = None) -> int:
    """Fetch directly from Gmail API (no cache) then classify unclassified emails."""
    repo = EmailRepository()

    try:
        # Use repository method with auto_resolve_date flag
        fetch_result = repo.fetch_from_gmail_and_save(
            user_id=user_id,
            max_results=max_results,
            before_date=after_date,
            auto_resolve_date=True  # Enable smart date resolution
        )
        print(f"[fetch-emails] Fetch status: {fetch_result.get('status', 'ok')}")

        classify_result = repo.classify_unclassified_emails(user_id=user_id, limit=classify_limit)
        print(f"[fetch-emails] Classified: {classify_result.get('classified', 0)}")

        return 0 if classify_result.get('status') == 'ok' else 1

    except Exception as exc:
        print(f"[fetch-emails] Failed: {exc}")
        return 1
```

**Pros**:

- ✅ Preserves explicit flow control in command
- ✅ Makes smart date logic available to API if needed
- ✅ Minimal changes
- ✅ Backward compatible

**Cons**:

- ⚠️ Still some duplication (manual fetch + classify calls)

### Option 3: Hybrid Approach (Best Balance)

Combine both options:

1. Move `_resolve_after_date()` to repository (Option 2)
2. Add optional `after_date` parameter to `fetch_and_process_emails()`
3. Make command use `fetch_and_process_emails()` (Option 1)

#### Changes:

```python
# In email_repository.py
def fetch_and_process_emails(
    self,
    user_id: str,
    max_results: int = 50,
    classify_limit: int = 200,
    after_date: str = None,
    auto_resolve_date: bool = True
) -> Dict:
    """Comprehensive email processing with optional date filtering."""

    # Auto-resolve after-date if enabled
    if auto_resolve_date and not after_date:
        after_date = self._resolve_after_date(user_id, after_date)

    # Fetch with date filter
    fetch_result = self.fetch_from_gmail_and_save(
        user_id=user_id,
        max_results=max_results,
        before_date=after_date
    )

    # ... rest of existing logic (classify, link, etc.)
```

```python
# In fetch_emails.py (simplified)
def run(user_id: str, max_results: int = 50, classify_limit: int = 200, after_date: str = None) -> int:
    """Fetch directly from Gmail API then classify unclassified emails."""
    repo = EmailRepository()

    try:
        result = repo.fetch_and_process_emails(
            user_id=user_id,
            max_results=max_results,
            classify_limit=classify_limit,
            after_date=after_date,
            auto_resolve_date=True  # Use smart date resolution
        )

        # Print summary
        print(f"[fetch-emails] Status: {result.get('status')}")
        print(f"[fetch-emails] Fetched: {result.get('emails_fetched', 0)}")
        print(f"[fetch-emails] Classified: {result.get('emails_classified', 0)}")

        return 0 if result.get('status') == 'ok' else 1
    except Exception as exc:
        print(f"[fetch-emails] Failed: {exc}")
        return 1
```

**Pros**:

- ✅ **Zero duplication** - single code path
- ✅ Command gets contact linking automatically
- ✅ Smart date resolution available to both flows
- ✅ API can optionally use date filtering
- ✅ Cleaner, more maintainable

**Cons**:

- ⚠️ Slightly more parameters to `fetch_and_process_emails()`

## Recommendation

**Implement Option 3 (Hybrid Approach)** for the following reasons:

1. **Eliminates all duplication** - Both flows use the same code path
2. **Preserves flexibility** - after-date can still be manually specified
3. **Adds smart defaults** - Auto-resolution prevents re-fetching same emails
4. **Better consistency** - Contact linking happens in both flows
5. **Easier maintenance** - One place to fix bugs, add features

### Implementation Steps

1. Move `_resolve_after_date()` logic from `fetch_emails.py` to `EmailRepository`
2. Add `after_date` and `auto_resolve_date` parameters to `fetch_and_process_emails()`
3. Update `fetch_from_gmail_and_save()` to use resolved date
4. Simplify `fetch_emails.py` to just call `fetch_and_process_emails()`
5. Test both flows to ensure identical behavior
6. Remove old date resolution code from command script

### Migration Path

This can be done incrementally:

1. **Phase 1**: Add new parameters without breaking existing behavior
2. **Phase 2**: Update command script to use new API
3. **Phase 3**: Remove duplicate code from command script
4. **Phase 4**: Add after-date support to web API if needed

## Conclusion

The current implementation has unnecessary duplication between the API and command flows. The recommended refactoring consolidates both flows to use `fetch_and_process_emails()` as the single source of truth, while adding flexible date filtering that was previously only available in the command script.

This will:

- **Reduce code** by ~30 lines
- **Improve consistency** between API and CLI
- **Fix bugs in one place** instead of two
- **Enable new features** (like date filtering in API) easily
