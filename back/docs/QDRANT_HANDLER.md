# Qdrant Handler

A clean handler for querying Qdrant vector database, following the same pattern as `db_handler.py`.

## Features

- **Collections**: List all collections
- **Info**: Get collection statistics
- **Scroll**: Paginate through points with metadata filtering
- **Search**: Vector similarity search with filters
- **Count**: Count points matching filters
- **Retrieve**: Get specific points by ID

## Configuration

Add to `config.yml`:

```yaml
qdrant:
  url: '/rkllm/qdrant_storage' # file path or http://localhost:6333
  collection_name: 'electric_parts'
  timeout: 30
```

## Python Usage

```python
from qdrant_handler import QdrantHandler

# Initialize
handler = QdrantHandler()

# Test connection
if handler.test_connection():
    print("Connected!")

# List collections
collections = handler.get_collections()
print(f"Collections: {collections}")

# Get collection info
info = handler.get_collection_info()
print(f"Points: {info['points_count']}")

# Scroll through points
result = handler.scroll_points(
    limit=100,
    filters={'vendor': 'Acme Corp', 'price_min': 10, 'price_max': 100},
    with_payload=True
)
for point in result['points']:
    print(point['payload'])

# Vector search
query_vector = [0.1, 0.2, ...]  # Your embedding
results = handler.search(
    query_vector=query_vector,
    limit=10,
    filters={'in_stock': True},
    score_threshold=0.7
)
for r in results:
    print(f"Score: {r['score']}, Data: {r['payload']}")

# Count
count = handler.count(filters={'vendor': 'Acme'})
print(f"Acme parts: {count}")

# Retrieve specific points
points = handler.retrieve(
    point_ids=[123, 456, 789],
    with_payload=True
)
```

## HTTP API Usage

Endpoint: `GET /api/qdrant`

### List Collections

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=collections"
```

Response:

```json
{
  "collections": ["electric_parts", "documents"],
  "count": 2
}
```

### Collection Info

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=info&collection=electric_parts"
```

Response:

```json
{
  "name": "electric_parts",
  "points_count": 1523,
  "vectors_count": 1523,
  "status": "green",
  "vector_size": 384
}
```

### Scroll Points

```bash
# Simple scroll
curl "http://127.0.0.1:8088/api/qdrant?action=scroll&limit=10"

# With filters
curl "http://127.0.0.1:8088/api/qdrant?action=scroll&limit=10&filters=%7B%22vendor%22%3A%22Acme%22%2C%22price_min%22%3A10%7D"

# Decoded filter: {"vendor":"Acme","price_min":10}
```

Response:

```json
{
  "points": [
    {
      "id": "12345",
      "payload": {
        "part_id": "P123",
        "part_name": "Widget",
        "price": 25.99,
        "vendor": "Acme"
      }
    }
  ],
  "next_offset": "opaque_token_for_next_page",
  "count": 10
}
```

### Vector Search

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=search&vector=%5B0.1%2C0.2%2C...%5D&limit=5"

# With filters and threshold
curl "http://127.0.0.1:8088/api/qdrant?action=search&vector=%5B...%5D&limit=5&score_threshold=0.7&filters=%7B%22in_stock%22%3Atrue%7D"
```

Response:

```json
{
  "results": [
    {
      "id": "12345",
      "score": 0.95,
      "payload": {
        "part_name": "Widget",
        "description": "A great widget"
      }
    }
  ],
  "count": 5
}
```

### Count Points

```bash
curl "http://127.0.0.1:8088/api/qdrant?action=count"

# With filters
curl "http://127.0.0.1:8088/api/qdrant?action=count&filters=%7B%22vendor%22%3A%22Acme%22%7D"
```

Response:

```json
{
  "count": 247
}
```

### Retrieve by IDs

```bash
# Comma-separated
curl "http://127.0.0.1:8088/api/qdrant?action=retrieve&ids=123,456,789"

# JSON array (URL encoded)
curl "http://127.0.0.1:8088/api/qdrant?action=retrieve&ids=%5B123%2C456%2C789%5D"
```

Response:

```json
{
  "points": [
    {
      "id": "123",
      "payload": {...}
    }
  ],
  "count": 3
}
```

## Filter Syntax

Filters support:

- **Exact match**: `{"field_name": "value"}`
- **Range filters**:
  - `{"price_min": 10}` - price >= 10
  - `{"price_max": 100}` - price <= 100
  - `{"score_gte": 0.7}` - score >= 0.7
  - `{"score_gt": 0.7}` - score > 0.7
  - `{"score_lte": 0.9}` - score <= 0.9
  - `{"score_lt": 0.9}` - score < 0.9

All conditions are combined with AND.

## Testing

Run the test script:

```bash
cd back
python test_qdrant_handler.py
```

## Integration with Chat

The Qdrant handler is now available for tool calls in the chat interface. You can add a `qdrant_search` tool to the LLM to enable semantic search capabilities.

Example tool definition:

```javascript
{
  type: 'function',
  function: {
    name: 'qdrant_search',
    description: 'Search the vector database for similar items',
    parameters: {
      type: 'object',
      properties: {
        query_text: { type: 'string' },
        limit: { type: 'integer', default: 10 },
        filters: { type: 'object' }
      },
      required: ['query_text']
    }
  }
}
```
