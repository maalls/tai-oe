/**
 * Vector search utilities for semantic search in Qdrant
 */

import { DB_API_URL } from './types';

export interface VectorSearchParams {
   collection: string;
   query: string;
   limit?: number;
   scoreThreshold?: number;
}

export interface VectorSearchResult {
   id: string | number;
   score: number;
   payload?: Record<string, any>;
}

/**
 * Fetch available Qdrant collections
 */
export async function fetchCollections(): Promise<string[]> {
   const baseUrl = DB_API_URL.replace('/api/csv/query', '');
   const url = new URL(`${baseUrl}/api/qdrant`);
   url.searchParams.set('action', 'collections');

   const response = await fetch(url.toString());
   if (!response.ok) {
      throw new Error(`Failed to fetch collections: HTTP ${response.status}`);
   }

   const data = await response.json();
   return data.collections || [];
}

/**
 * Execute semantic vector search
 */
export async function executeVectorSearch(
   params: VectorSearchParams
): Promise<VectorSearchResult[]> {
   const { collection, query, limit = 10, scoreThreshold = 0 } = params;

   if (!collection) throw new Error('Collection is required');
   if (!query.trim()) throw new Error('Search query is required');

   const baseUrl = DB_API_URL.replace('/api/csv/query', '');

   // Step 1: Generate embedding from query text
   const embeddingUrl = new URL(`${baseUrl}/api/embeddings`);
   embeddingUrl.searchParams.set('text', query);

   const embeddingResponse = await fetch(embeddingUrl.toString());
   if (!embeddingResponse.ok) {
      const text = await embeddingResponse.text();
      throw new Error(`Failed to generate embedding: ${text}`);
   }

   const embeddingData = await embeddingResponse.json();
   if (!embeddingData.vector) {
      throw new Error('No vector returned from embedding service');
   }

   // Step 2: Search Qdrant with the vector
   const searchUrl = new URL(`${baseUrl}/api/qdrant`);
   searchUrl.searchParams.set('action', 'search');
   searchUrl.searchParams.set('collection', collection);
   searchUrl.searchParams.set('vector', JSON.stringify(embeddingData.vector));
   searchUrl.searchParams.set('limit', String(limit));
   if (scoreThreshold > 0) {
      searchUrl.searchParams.set('score_threshold', String(scoreThreshold));
   }

   const response = await fetch(searchUrl.toString());
   if (!response.ok) {
      const text = await response.text();
      throw new Error(`Search failed: HTTP ${response.status} - ${text}`);
   }

   const data = await response.json();
   return data.results || [];
}

/**
 * Format vector search results as HTML table
 */
export function formatVectorResultsAsTable(results: VectorSearchResult[], query: string): string {
   if (results.length === 0) {
      return '❌ No results found for your search query.';
   }

   let html =
      '<div class="overflow-x-auto"><table class="min-w-full border-collapse border border-gray-300"><thead class="bg-purple-100"><tr>';

   // Get column headers from first result
   if (results[0]?.payload) {
      const headers = Object.keys(results[0].payload);
      html += '<th class="border border-gray-300 px-2 py-1 text-left font-semibold">Score</th>';
      for (const header of headers) {
         if (!header.startsWith('_')) {
            html += `<th class="border border-gray-300 px-2 py-1 text-left font-semibold">${header}</th>`;
         }
      }
   }
   html += '</tr></thead><tbody>';

   // Add rows
   for (const result of results) {
      html += '<tr class="hover:bg-purple-50">';
      const score = result.score ? result.score.toFixed(4) : 'N/A';
      html += `<td class="border border-gray-300 px-2 py-1 font-mono text-sm text-purple-600">${score}</td>`;

      if (result.payload) {
         for (const [key, value] of Object.entries(result.payload)) {
            if (!key.startsWith('_')) {
               const displayValue =
                  value === null ? '<em class="text-gray-500">null</em>' : String(value);
               html += `<td class="border border-gray-300 px-2 py-1 text-sm">${displayValue}</td>`;
            }
         }
      }
      html += '</tr>';
   }

   html += '</tbody></table></div>';
   html += `<div class="text-sm text-gray-600 mt-2">Found ${results.length} result(s) for: <strong>${query}</strong></div>`;

   return html;
}
