# Direct Query Feature - Implementation Test Cases

## Test Case 1: Basic Query Execution

**Steps:**

1. Expand "📊 Direct Database Query" form
2. Select `fabdis_commerce` table
3. Keep Columns as `*`
4. Leave WHERE clause empty
5. Set Limit to 5
6. Click "▶️ Execute Query"

**Expected Result:**

- Query executes
- First 5 rows from `fabdis_commerce` display as HTML table
- Table shows as assistant message in chat
- Form clears for new query
- Results persist in message history

---

## Test Case 2: Query with WHERE Clause

**Steps:**

1. Expand form
2. Select `fabdis_commerce`
3. Columns: `*`
4. WHERE: `tarif > 100`
5. Limit: 10
6. Click Execute

**Expected Result:**

- Displays products with tarif > 100
- Limited to 10 rows
- Table renders with proper formatting

---

## Test Case 3: Sorting

**Steps:**

1. Expand form
2. Select `fabdis_commerce`
3. Columns: `designation, tarif`
4. WHERE: empty
5. Sort By: `tarif`
6. Sort Order: `DESC`
7. Limit: 20

**Expected Result:**

- Shows top 20 products sorted by tarif descending
- Only shows designation and tarif columns
- Table formats correctly

---

## Test Case 4: Error Handling - No Table Selected

**Steps:**

1. Expand form
2. Leave table as "--Select table--"
3. Click Execute

**Expected Result:**

- Button is disabled (grayed out)
- No query executed
- Error message: "Please select a table" shows in red box

---

## Test Case 5: Form Persistence

**Steps:**

1. Execute a query successfully
2. Check chat messages

**Expected Result:**

- Result displays as table in chat
- Form fields cleared
- Message persists when page reloaded
- Message appears in localStorage history

---

## Test Case 6: Column Selection

**Steps:**

1. Expand form
2. Select `fabdis_commerce`
3. Columns: `refciale, libelle240, tarif`
4. Limit: 5

**Expected Result:**

- Only specified columns shown in table
- No need to list all available columns

---

## Test Case 7: Combined Parameters

**Steps:**

1. Select `fabdis_commerce`
2. Columns: `marque, libelle240, tarif`
3. WHERE: `tarif BETWEEN 50 AND 200`
4. Sort By: `marque`
5. Sort Order: `ASC`
6. Limit: 15

**Expected Result:**

- Filters by price range
- Shows only selected columns
- Sorts by brand alphabetically
- Limits to 15 rows

---

## Test Case 8: Loading State

**Steps:**

1. Execute a query
2. Observe button during execution

**Expected Result:**

- Button shows "⏳ Executing..."
- Button is disabled during query
- Returns to normal after completion

---

## Test Case 9: Error Response from Backend

**Steps:**

1. Execute query with invalid WHERE clause: `tarif > "invalid"`
2. Observe form

**Expected Result:**

- Query fails on backend
- Error message displays in red box in form
- User can retry with corrected parameters

---

## Test Case 10: HTML Table Display in Chat

**Steps:**

1. Execute any query successfully
2. Observe table in chat area
3. Scroll table if results are wide

**Expected Result:**

- Table displays with:
  - Gray header row (#f3f4f6)
  - Gray borders (#e5e7eb)
  - 8px padding around content
  - Left-aligned text
  - Overflow handling for wide tables
- Table integrates seamlessly with chat messages

---

## Implementation Notes

### URL Construction

```
GET http://localhost:8088/query
  ?table=fabdis_commerce
  &columns=refciale,libelle240,tarif
  &where=tarif > 100
  &sortBy=tarif DESC
  &limit=10
```

### Response Format

```json
{
  "columns": ["refciale", "libelle240", "tarif"],
  "rows": [
    { "refciale": "ABC123", "libelle240": "Product A", "tarif": 150 },
    { "refciale": "ABC124", "libelle240": "Product B", "tarif": 175 }
  ],
  "count": 2,
  "offset": 0,
  "limit": 10
}
```

### HTML Table Generated

```html
<table style="width:100%; border-collapse: collapse; margin: 8px 0;">
  <thead>
    <tr style="background-color: #f3f4f6;">
      <th
        style="border: 1px solid #e5e7eb; padding: 8px; text-align: left; font-weight: 600;"
      >
        refciale
      </th>
      <th
        style="border: 1px solid #e5e7eb; padding: 8px; text-align: left; font-weight: 600;"
      >
        libelle240
      </th>
      <th
        style="border: 1px solid #e5e7eb; padding: 8px; text-align: left; font-weight: 600;"
      >
        tarif
      </th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom: 1px solid #e5e7eb;">
      <td style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">
        ABC123
      </td>
      <td style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">
        Product A
      </td>
      <td style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">
        150
      </td>
    </tr>
    ...
  </tbody>
</table>
```

---

## Key Features Verified

✅ Form validation (table required)
✅ Parameter optional support (columns, where, sortBy, sortOrder all optional)
✅ HTML table rendering with v-html directive
✅ Message persistence via useChat composable
✅ Loading state management
✅ Error display
✅ Form clearing after successful query
✅ Backward compatibility with existing chat functionality
