# Qdrant Handler - Quick Start Guide

## What's New

You now have a complete Qdrant vector database handler similar to your existing `db_handler`. It allows querying semantic vectors stored in Qdrant, which is perfect for RAG and semantic search capabilities.

## Starting the Backend

```bash
cd back/
python3 src/rag/rag.py
```

The server will initialize both handlers:

- Database handler for SQL queries
- **Qdrant handler for vector searches** ✨

## Testing the Qdrant Endpoint

### List all collections:

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=collections"
```

### Get collection info:

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=info&collection=electric_parts"
```

### Count items in a collection:

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=count"
```

### Scroll through items with filters:

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=scroll&limit=10&filters=%7B%22vendor%22%3A%22Acme%22%7D"
```

## Using in Chat

The Qdrant handler is ready to be added as a tool in your chat interface. See `front/vite/src/qdrant-chat-integration.ts` for a complete example.

To add vector search to your chat:

1. Import the `qdrantTool` definition from the integration file
2. Add it to your `tools` array in ChatPage.vue
3. Add the handler in `executeToolCalls()`

Example:

```typescript
if (name === 'qdrant_search') {
  const result = await executeQdrantSearch(args);
  // Add tool result to messages...
}
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  Chat Interface (Vue 3)                     │
│  - Send text message                        │
│  - LLM detects need for tool calls          │
└─────────────────────────────────────────────┘
              ↓ POST /v1/chat/completions
┌─────────────────────────────────────────────┐
│  LLM Server (192.168.1.5:1234)              │
│  - Process conversation                     │
│  - Detect tool calls                        │
└─────────────────────────────────────────────┘
              ↓ GET /api/csv/query or /api/qdrant
┌─────────────────────────────────────────────┐
│  RAG Server (127.0.0.1:8088)                │
│  ┌────────────────────────────────────────┐ │
│  │ RequestHandlers                        │ │
│  │ - handle_query() → DB queries          │ │
│  │ - handle_qdrant_query() → Qdrant ops  │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │ DatabaseHandler (PostgreSQL)           │ │
│  │ - SQL execution                        │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │ QdrantHandler (Vector DB)              │ │
│  │ - Search, scroll, count operations     │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## Features

✅ **Scroll** - Paginate through vector points with metadata filtering  
✅ **Search** - Semantic similarity search with similarity scoring  
✅ **Count** - Count points matching metadata filters  
✅ **Retrieve** - Fetch specific points by ID  
✅ **Info** - Get collection statistics  
✅ **Collections** - List all available collections

## Configuration

Edit `back/config.yml`:

```yaml
qdrant:
  url: '/rkllm/qdrant_storage' # Local file storage or http://host:port
  collection_name: 'electric_parts' # Default collection
  timeout: 30 # Request timeout in seconds
```

## Example: RAG Workflow

1. **User asks**: "What products are similar to a 5V power supply?"

2. **Chat sends to LLM** with available tools: `db_query` and `qdrant_search`

3. **LLM decides** to use `qdrant_search` with:

   ```json
   {
     "query_vector": [0.12, 0.45, 0.78, ...],
     "limit": 5,
     "filters": {"in_stock": true, "price_max": 50}
   }
   ```

4. **Backend searches** vector DB and returns top 5 similar items

5. **LLM provides answer**: "I found these 5 similar power supplies: ..."

6. **User sees** relevant products ranked by similarity

## Troubleshooting

**"Collection not found"**

- Ensure Qdrant server is running and has data loaded
- Check collection name in `config.yml` matches actual collections

**"Connection failed"**

- Verify `url` in config points to correct Qdrant location
- If using HTTP, ensure server is accessible: `curl http://localhost:6333/health`

**"Invalid filter"**

- Check filter JSON is properly formatted
- Use exact field names from your payload schema

## Files Added/Modified

```
✅ back/src/rag/qdrant_handler.py          - New handler (390 lines)
✅ back/src/rag/QDRANT_HANDLER.md          - Full API docs
✅ back/config.yml                         - Added qdrant config section
✅ back/src/rag/handlers.py                - Integrated handle_qdrant_query()
✅ back/src/rag/rag.py                     - Wired /api/qdrant endpoint
✅ front/vite/src/qdrant-chat-integration.ts - Chat tool examples
✅ QDRANT_IMPLEMENTATION.md                - Implementation summary
```

## Next Steps

1. ✅ Start backend: `python3 src/rag/rag.py`
2. ✅ Start frontend: `npm run dev` (from front/vite)
3. ✅ Test Qdrant endpoint in browser: `http://127.0.0.1:8088/api/qdrant?action=collections`
4. ✅ Add `qdrant_search` tool to chat (see integration example)
5. ✅ Chat with vector search enabled!

## Performance Notes

- Vector search is typically <100ms for moderate collections
- Scroll with pagination is efficient for large datasets
- Filters are applied server-side, reducing data transfer
- All operations support configurable limits (1-1000)

---

**Questions?** Check `QDRANT_HANDLER.md` for detailed API documentation or `qdrant-chat-integration.ts` for code examples.
