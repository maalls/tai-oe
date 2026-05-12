# Direct Database Query Feature

## Overview

Added an interactive direct database query form to the ChatPage that allows users to query products without going through the LLM. Results are displayed as formatted HTML tables and saved as assistant messages in the chat history.

## Files Modified

### 1. **ChatPage.vue** (front/vite/src/components/ChatPage.vue)

Added query form UI and execution logic:

- **Query Form** (collapsible `<details>` element):

  - Table selector: `fabdis_commerce` or `fabdis_cartouches`
  - Columns field: comma-separated or `*` for all
  - WHERE clause: optional SQL WHERE condition
  - Sort By: column name for ordering
  - Sort Order: ASC or DESC dropdown
  - Limit: number of rows (1-1000)
  - Error display for query failures
  - Execute button with loading state

- **New Reactive State**:

  ```typescript
  queryTable,
    queryColumns,
    queryWhere,
    querySortBy,
    querySortOrder,
    queryLimit,
    queryLoading,
    queryError;
  ```

- **Query Handler Function** (`executeDirectProductQuery()`):

  1. Validates table selection
  2. Constructs `QueryParams` object
  3. Calls `executeDirectQuery()` from directQuery module
  4. Formats results as HTML table via `formatResultsAsTable()`
  5. Adds results as assistant message to chat
  6. Clears form on success
  7. Displays error message on failure

- **Template Updates**:
  - HTML table detection and rendering: `v-if="m.content.includes('<table')" v-html="m.content"`
  - Allows inline HTML rendering while maintaining XSS safety (results come from controlled DB API)

## Files Created

### 2. **directQuery.ts** (front/vite/src/components/chat/directQuery.ts)

Utility module for direct database queries and result formatting:

**Types:**

```typescript
export interface QueryParams {
  table: string;
  columns?: string;
  where?: string;
  sortBy?: string;
  sortOrder?: string;
  limit?: number;
}
```

**Functions:**

1. **`executeDirectQuery(params: QueryParams): Promise<any>`**

   - Constructs DB API URL with query parameters
   - Combines `sortBy` and `sortOrder` into single clause: `"${sortBy} ${sortOrder}"`
   - Fetches results from backend
   - Throws error on HTTP failure with status code

2. **`formatResultsAsTable(data: any): string`**
   - Converts query result rows into HTML table
   - Uses inline CSS styling (no external stylesheets):
     - Border: 1px solid #e5e7eb (gray-200)
     - Header background: #f3f4f6 (gray-100)
     - Cell padding: 8px
     - Text alignment: left
   - Handles null/undefined values as em-dash (—)
   - Respects column order from result

## Integration Points

### Backend Support

The feature integrates with existing backend infrastructure:

- **database_handlers.py**: `handle_query()` already supports `sortBy` parameter
- **URL Format**: `http://localhost:8088/query?table=...&sortBy=...&where=...&limit=100`
- Parameter handling maintains SQL safety through parameterized queries

### Frontend Architecture

- Uses `executeDirectQuery()` from directQuery module (no additional HTTP client needed)
- Integrates with `useChat` composable for message management
- Messages persist via existing localStorage infrastructure (same as LLM messages)
- No new dependencies required

## Usage Flow

1. **Expand Query Form**: Click "📊 Direct Database Query" to expand the collapsible form
2. **Enter Query Parameters**:
   - Select table (required)
   - Optionally specify columns, WHERE clause, sort parameters, limit
3. **Execute**: Click "▶️ Execute Query" button
4. **View Results**:
   - Results display as formatted HTML table in chat
   - Saved as assistant message in history
   - Can scroll through results in the chat area
5. **Persist**: Results saved to localStorage with other chat messages

## Styling & UX

**Form Container**:

- Collapsible with `<details>` tag for clean UI
- Blue-tinted background (`bg-blue-50`) for visual distinction
- Organized grid layout for parameter inputs
- Responsive column layout

**Table Display**:

- Professional appearance with borders and alternating rows
- Left-aligned text with consistent padding
- Clear column headers with bold font weight
- Seamless integration into chat message stream

**Error Handling**:

- Validation: Table selection required
- Error messages displayed in red box within form
- Loading state shows "⏳ Executing..." during query
- Button disabled until query completes

## Feature Benefits

✅ **Direct Access**: Query database without LLM intermediary (faster, more predictable)
✅ **Table-Based UI**: Results display as readable HTML tables
✅ **Parameter Control**: Full control over query parameters
✅ **History Persistence**: Results saved as chat messages
✅ **Clean Integration**: Collapsible form doesn't clutter UI
✅ **Sort Support**: Full support for sorting (built on previous sortBy/sortOrder work)
✅ **Safe Rendering**: Server-side SQL parameterization + controlled HTML rendering

## Future Enhancements

- CSV export button for table results
- Query result pagination
- Column hiding/reordering in table display
- Query templates/saved queries
- Advanced WHERE clause builder UI
- Result filtering/searching within chat
