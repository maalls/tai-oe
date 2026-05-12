// @ts-nocheck
import { ref, onMounted, watch, nextTick } from 'vue';
import { apiUrl } from './utils/api';

type ChatMessage = {
   role: 'system' | 'user' | 'assistant' | 'tool';
   content: string | null;
   name?: string;
   tool_call_id?: string;
   tool_calls?: Array<{
      id: string;
      type: 'function';
      function: { name: string; arguments: string };
   }>;
};

const LLM_API_URL = 'http://localhost:1234/v1/chat/completions';
const QDRANT_API_URL = apiUrl('/api/qdrant');

// Example: Add this tool to your tools array in ChatPage.vue
const qdrantTool = {
   type: 'function',
   function: {
      name: 'qdrant_search',
      description:
         'Search the vector database for semantically similar items using vector similarity. Provide a vector embedding or let the model generate one from a description.',
      parameters: {
         type: 'object',
         properties: {
            query_vector: {
               type: 'array',
               items: { type: 'number' },
               description: 'Query embedding vector (dense float array)',
            },
            limit: {
               type: 'integer',
               minimum: 1,
               maximum: 1000,
               default: 10,
               description: 'Maximum number of results',
            },
            score_threshold: {
               type: 'number',
               minimum: 0,
               maximum: 1,
               description: 'Minimum similarity score (optional)',
            },
            filters: {
               type: 'object',
               description:
                  'Metadata filters (e.g., {"vendor": "Acme", "price_min": 10, "price_max": 100})',
            },
            collection_name: {
               type: 'string',
               description: 'Collection to search (optional, uses default if omitted)',
            },
         },
         required: ['query_vector'],
      },
   },
};

// Add to your tools array:
// const tools = [
//   { ... db_query tool ... },
//   qdrantTool,
// ];

// Handler for qdrant_search tool calls
async function executeQdrantSearch(args: any) {
   const { query_vector, limit = 10, score_threshold, filters, collection_name } = args;

   if (!query_vector || !Array.isArray(query_vector)) {
      throw new Error('query_vector must be an array of numbers');
   }

   const url = new URL(QDRANT_API_URL);
   url.searchParams.set('action', 'search');
   url.searchParams.set('vector', JSON.stringify(query_vector));
   url.searchParams.set('limit', String(limit));

   if (score_threshold !== undefined) {
      url.searchParams.set('score_threshold', String(score_threshold));
   }

   if (filters && Object.keys(filters).length > 0) {
      url.searchParams.set('filters', JSON.stringify(filters));
   }

   if (collection_name) {
      url.searchParams.set('collection', collection_name);
   }

   const resp = await fetch(url.toString());
   if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Qdrant search error ${resp.status}: ${text}`);
   }

   return await resp.json();
}

// Integration example for tool execution
// In your executeToolCalls function, add:
//
// if (name === 'qdrant_search') {
//    try {
//       const args = safeParseArgs(argStr);
//       const result = await executeQdrantSearch(args);
//       messages.value.push({
//          role: 'tool',
//          name: 'qdrant_search',
//          tool_call_id: tc.id,
//          content: JSON.stringify(result),
//       });
//    } catch (e: any) {
//       messages.value.push({
//          role: 'tool',
//          name: 'qdrant_search',
//          tool_call_id: tc.id,
//          content: JSON.stringify({ error: String(e?.message || e) }),
//       });
//    }
// }

// Example conversation flow:
//
// User: "Find products similar to a USB cable"
//
// LLM thinks: "I need to:
//   1. Understand the user is asking for semantic search
//   2. Generate or use an embedding for 'USB cable'
//   3. Call qdrant_search with that vector
//   4. Return the results to the user"
//
// LLM calls tool: qdrant_search(query_vector=[...], limit=5, filters={"in_stock": true})
//
// Backend: Performs vector similarity search in Qdrant
//
// Returns: Top 5 semantically similar products in stock
//
// LLM follows up: "I found these USB-related products: [list]"
