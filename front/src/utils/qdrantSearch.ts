import { apiUrl } from './api';

const EMBEDDINGS_API_URL = apiUrl('embeddings');
const QDRANT_API_URL = apiUrl('qdrant');

export interface QdrantSearchOptions {
   collection: string;
   query: string;
   limit?: number;
   with_payload?: boolean;
}

export interface QdrantScrollOptions {
   collection: string;
   limit?: number;
   offset?: string | null;
   filters?: Record<string, any>;
   with_payload?: boolean;
   with_vectors?: boolean;
}

export interface QdrantScrollResult {
   points: any[];
   next_offset?: string | null;
   count: number;
   error?: string;
}

export interface QdrantSearchResult {
   id: string | number;
   score: number;
   payload?: any;
}

export class QdrantSearch {
   /**
    * Perform a semantic search in Qdrant collection.
    * First generates embeddings from text, then searches Qdrant with the vector.
    */
   static async search(options: QdrantSearchOptions): Promise<QdrantSearchResult[]> {
      const { collection, query, limit = 10, with_payload = true } = options;

      if (!query.trim() || !collection) {
         throw new Error('Query and collection are required');
      }

      // Step 1: Generate embedding from text
      const embeddingUrl = new URL(EMBEDDINGS_API_URL);
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
      const searchUrl = new URL(QDRANT_API_URL);
      searchUrl.searchParams.set('action', 'search');
      searchUrl.searchParams.set('collection', collection);
      searchUrl.searchParams.set('vector', JSON.stringify(embeddingData.vector));
      searchUrl.searchParams.set('limit', String(limit));
      searchUrl.searchParams.set('with_payload', String(with_payload));

      const searchResponse = await fetch(searchUrl.toString());
      if (!searchResponse.ok) {
         const text = await searchResponse.text();
         throw new Error(`Search failed: ${text}`);
      }

      const searchData = await searchResponse.json();
      return searchData.results || [];
   }
}

export class QdrantScroll {
   /**
    * Scroll points with optional filters and pagination.
    */
   static async scroll(options: QdrantScrollOptions): Promise<QdrantScrollResult> {
      const {
         collection,
         limit = 100,
         offset = null,
         filters,
         with_payload = true,
         with_vectors = false,
      } = options;

      if (!collection) {
         throw new Error('Collection is required');
      }

      const url = new URL(QDRANT_API_URL);
      url.searchParams.set('action', 'scroll');
      url.searchParams.set('collection', collection);
      url.searchParams.set('limit', String(limit));
      url.searchParams.set('with_payload', String(with_payload));
      url.searchParams.set('with_vectors', String(with_vectors));
      if (offset) {
         url.searchParams.set('offset', offset);
      }
      if (filters) {
         url.searchParams.set('filters', JSON.stringify(filters));
      }

      const response = await fetch(url.toString());
      if (!response.ok) {
         const text = await response.text();
         throw new Error(`Scroll failed: ${text}`);
      }

      const data = await response.json();
      return {
         points: data.points || [],
         next_offset: data.next_offset ?? null,
         count: data.count ?? (data.points ? data.points.length : 0),
         error: data.error,
      };
   }
}
