# Quote Extraction Pathways - Price Issue Analysis

## Problem Statement

When extracting a quote from the Quote View ("Extract From Source" button), prices are not extracted from Qdrant. However, when extracting from the Source View ("Scan RFQ" button), prices work correctly (or can be filled manually).

## Two Extraction Pathways

### Pathway 1: Quote View - "Extract From Source" Button ❌ NO PRICES

**Frontend**: `QuotePage.vue` → `generateQuote()` (line 435)
**Endpoint**: `POST /api/opportunity/{id}/rfq/generate`
**Backend Handler Chain**:

1. `handlers.handle_generate_quote_for_opportunity()` → `opportunity.py:255`
2. Calls `opportunity.handle_generate_quote_for_opportunity()`
3. Calls `_extract_and_enrich_rfp_data()` (line 490)
4. Qdrant enrichment happens here BUT...
5. Returns response with `"draft": rfp_data`

**Frontend Processing** (line 463-470):

```typescript
const normalizedProducts = (result?.draft?.products || []).map((p: any) => ({
  ...p,
  sku: p.sku || '',
  description: p.description || p.title || '',
  quantity: p.quantity || 1,
  price: p.price || 0, // ← Problem: backend price is null/undefined
  tax_rate: p.tax_rate || 20,
  manufacturer: p.manufacturer || '',
}));
```

### Pathway 2: Source View - "Scan RFQ" Button ✓ HAS PRICES

**Frontend**: `SourcePage.vue` → `scanAttachmentForRFQ()` (line 169)
**Endpoint**: `POST /api/document/extract-rfp`
**Backend Handler**:

1. `handlers.handle_extract_rfp_from_document()` → `business_handler.py:1381`
2. Only calls `extract_rfp_from_text()`
3. **NO Qdrant enrichment**
4. Returns raw extracted data

## Root Cause: Missing Qdrant in Pathway 2

`handle_extract_rfp_from_document()` (business_handler.py:1381) does NOT enrich with Qdrant prices:

```python
# It only does:
rfp_data = extract_rfp_from_text(message_clean)  # No Qdrant
company_data = extract_company_from_text(message_clean)  # No Qdrant

# It should also do (like Pathway 1):
rfp_data = self.opportunity_repository._extract_and_enrich_rfp_data(
    message_clean,
    pre_extracted_data=rfp_data
)
```

## Secondary Issue: Pathway 1 Price Not Found

In `opportunity.py:540-555`, when Qdrant finds no matches:

```python
if product['qdrant_matches']:
    product['price_found'] = True
    product['price'] = product['qdrant_matches'][0]['payload'].get('tarif')
else:
    product['price_found'] = False
    product['price'] = None  # ← This becomes 0 in frontend
```

**Possible reasons Qdrant finds no matches**:

1. **Field name mismatch**: Filters use `'marque'` and `'refciale'` but extracted data might use different names
2. **Empty filters**: If both manufacturer and SKU are missing, `continue` is hit (line 544)
3. **Qdrant collection is wrong collection_name**
4. **Data mismatch**: Extracted values don't match what's indexed in Qdrant

## Recommended Fixes

### Fix 1: Add Qdrant Enrichment to Pathway 2 (Quick Fix) ⭐

In `handle_extract_rfp_from_document()` (business_handler.py:1381), after extraction:

```python
# Extract RFP data
rfp_data = extract_rfp_from_text(message_clean)
if not isinstance(rfp_data, dict):
    rfp_data = {"products": [], "contact": {}}

# ADD THIS: Enrich with Qdrant prices (same as Pathway 1)
rfp_data = self.opportunity_repository._extract_and_enrich_rfp_data(
    message_clean,
    pre_extracted_data=rfp_data
)
```

This brings consistency: both pathways use `_extract_and_enrich_rfp_data()`.

### Fix 2: Consolidate to Single Function (Refactoring) ⭐⭐

Create a shared extraction function that both pathways use:

```python
def extract_and_enrich_rfp(content: str, pre_extracted_data: Dict = None) -> Dict:
    """Extract and enrich RFP data with Qdrant pricing."""
    # This already exists as _extract_and_enrich_rfp_data()
    # Make it public and use from both pathways
```

### Fix 3: Debug Qdrant Matching (Root Cause Analysis)

Add logging to `_extract_and_enrich_rfp_data()`:

```python
for product in rfp_data.get('products', []) or []:
    filters = {}
    if product.get('manufacturer'):
        filters['marque'] = product['manufacturer']
    if product.get('sku'):
        filters['refciale'] = product['sku']

    print(f"[DEBUG] Searching Qdrant with filters: {filters}")

    if not filters:
        print(f"[DEBUG] Product {product.get('description')} has no filters, skipping")
        continue

    match = qdrant_handler.scroll_points(...)
    print(f"[DEBUG] Found {len(match.get('points', []))} matches for {product.get('sku')}")
```

## Architecture Recommendation

**Current State**: Two separate extraction paths (confusing, bug-prone)

**Recommended State**: Single unified extraction pipeline

```
Both UI pathways (Quote View + Source View)
    ↓
    Call same backend function: extract_and_enrich_rfp_data()
    ├─ Extract text/structured data via LLM
    ├─ Normalize field names (part_number → sku, etc.)
    ├─ Enrich with Qdrant pricing
    └─ Return complete RFP data
```

## Implementation Priority

1. **Quick Fix**: Add Qdrant enrichment to `handle_extract_rfp_from_document()`
2. **Refactor**: Extract shared logic to reduce duplication
3. **Debug**: Add logging to understand why Qdrant finds no matches in Pathway 1

## Files to Modify

### Required for Quick Fix:

- `/Users/malo/Documents/Projects/rkllm-server/external/rag/back/src/controller/business_handler.py` (line ~1450)

### Recommended for Refactoring:

- Make `_extract_and_enrich_rfp_data()` public (remove `_` prefix)
- Call it from both `handle_generate_quote_for_opportunity()` and `handle_extract_rfp_from_document()`
- Add debug logging for Qdrant matching
