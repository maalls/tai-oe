"""Qdrant vector database request handlers."""

import json
from typing import Optional, Dict

from src.controller.qdrant_handler import QdrantHandler


class QdrantHandlers:
    """Handlers for Qdrant vector database operations."""
    
    def __init__(self, qdrant_handler: Optional[QdrantHandler] = None):
        self.qdrant_handler = qdrant_handler
    
    def handle_qdrant_query(self, qs: Dict) -> Dict:
        """Handle Qdrant vector database query requests.
        
        Query parameters:
            action: Action to perform - 'collections', 'info', 'scroll', 'search', 'count', 'retrieve', 'textsearch'
            
            For 'collections':
                (no params) - returns list of all collections
            
            For 'info':
                collection: Collection name (optional, uses default)
            
            For 'scroll':
                collection: Collection name (optional, uses default)
                limit: Max points (default 100, max 1000)
                offset: Pagination offset from previous response
                with_payload: Include payload (default true)
                with_vectors: Include vectors (default false)
                filters: JSON object with metadata filters
            
            For 'search':
                collection: Collection name (optional, uses default)
                vector: JSON array with query vector (required)
                limit: Max results (default 10, max 1000)
                score_threshold: Minimum similarity score (optional)
                with_payload: Include payload (default true)
                with_vectors: Include vectors (default false)
                filters: JSON object with metadata filters
            
            For 'count':
                collection: Collection name (optional, uses default)
                filters: JSON object with metadata filters
            
            For 'retrieve':
                collection: Collection name (optional, uses default)
                ids: Comma-separated point IDs or JSON array
                with_payload: Include payload (default true)
                with_vectors: Include vectors (default false)
            
            For 'textsearch':
                collection: Collection name (required)
                field: Payload field to search in (required)
                pattern: Text pattern to match (required)
                mode: Match mode - 'contains', 'startswith', 'exact', 'ilike' (default: 'contains')
                limit: Max results (default 100)
        
        Returns:
            Dict with query results
        """
        if not self.qdrant_handler:
            return {"error": "Qdrant handler not configured"}
        
        print(f"Received Qdrant query with parameters: {qs}")
        action = (qs.get('action') or ['info'])[0]
        
        try:
            if action == 'collections':
                collections = self.qdrant_handler.get_collections()
                return {"collections": collections, "count": len(collections)}
            
            elif action == 'info':
                collection = (qs.get('collection') or [None])[0]
                info = self.qdrant_handler.get_collection_info(collection)
                if info is None:
                    return {"error": "Collection not found or error getting info"}
                return info
            
            elif action == 'scroll':
                collection = (qs.get('collection') or [None])[0]
                limit = int((qs.get('limit') or ['100'])[0])
                offset = (qs.get('offset') or [None])[0]
                with_payload = (qs.get('with_payload') or ['true'])[0].lower() == 'true'
                with_vectors = (qs.get('with_vectors') or ['false'])[0].lower() == 'true'
                search_query = (qs.get('q') or [None])[0]  # Optional semantic search query
                
                filters = None
                filters_raw = (qs.get('filters') or [None])[0]
                pattern_filters = {}  # Filters that need pattern matching
                exact_filters = {}    # Filters that use exact matching
                
                if filters_raw:
                    filters = json.loads(filters_raw)
                    # Separate pattern filters from exact filters
                    # Pattern matching is used for text fields like refciale
                    for key, value in filters.items():
                        if isinstance(value, str) and key in [
                            'refciale',
                            'libelle240',
                            'marque',
                            'tarif',
                            'family_codes'
                        ]:
                            # Use pattern matching for these text fields
                            pattern_filters[key] = value
                        else:
                            # Use exact matching for everything else
                            exact_filters[key] = value
                
                # If search query (q) is provided, combine vector search with filters
                if search_query:
                    return self._combined_search(
                        collection=collection,
                        query=search_query,
                        pattern_filters=pattern_filters,
                        exact_filters=exact_filters,
                        limit=limit,
                        with_payload=with_payload,
                        with_vectors=with_vectors
                    )
                
                # If we have pattern filters, use client-side filtering
                if pattern_filters:
                    # Scroll through collection and filter client-side
                    all_points = []
                    scroll_offset = offset
                    max_scroll = 10000  # Safety limit
                    fetched = 0
                    
                    while len(all_points) < limit and fetched < max_scroll:
                        batch = self.qdrant_handler.scroll_points(
                            limit=min(100, max_scroll - fetched),
                            offset=scroll_offset,
                            filters=exact_filters if exact_filters else None,
                            collection_name=collection,
                            with_payload=with_payload,
                            with_vectors=with_vectors
                        )
                        
                        if not batch.get('points'):
                            break
                        
                        # Filter points by patterns
                        for point in batch['points']:
                            if self._matches_all_patterns(point, pattern_filters):
                                all_points.append(point)
                                if len(all_points) >= limit:
                                    break
                        
                        scroll_offset = batch.get('next_offset')
                        fetched += len(batch['points'])
                        
                        if not scroll_offset or len(batch['points']) < 100:
                            break
                    
                    return {
                        "points": all_points,
                        "next_offset": None,  # Pattern filtering doesn't support pagination
                        "count": len(all_points)
                    }
                else:
                    # Use standard Qdrant scroll with exact filters
                    result = self.qdrant_handler.scroll_points(
                        limit=limit,
                        offset=offset,
                        filters=exact_filters if exact_filters else None,
                        collection_name=collection,
                        with_payload=with_payload,
                        with_vectors=with_vectors
                    )
                    return result
            
            elif action == 'search':
                collection = (qs.get('collection') or [None])[0]
                vector_raw = (qs.get('vector') or [None])[0]
                
                if not vector_raw:
                    return {"error": "Missing 'vector' parameter for search"}
                
                query_vector = json.loads(vector_raw)
                if not isinstance(query_vector, list):
                    return {"error": "Vector must be a JSON array"}
                
                limit = int((qs.get('limit') or ['10'])[0])
                score_threshold_raw = (qs.get('score_threshold') or [None])[0]
                score_threshold = float(score_threshold_raw) if score_threshold_raw else None
                with_payload = (qs.get('with_payload') or ['true'])[0].lower() == 'true'
                with_vectors = (qs.get('with_vectors') or ['false'])[0].lower() == 'true'
                
                filters = None
                filters_raw = (qs.get('filters') or [None])[0]
                if filters_raw:
                    filters = json.loads(filters_raw)
                
                results = self.qdrant_handler.search(
                    query_vector=query_vector,
                    limit=limit,
                    filters=filters,
                    collection_name=collection,
                    score_threshold=score_threshold,
                    with_payload=with_payload,
                    with_vectors=with_vectors
                )
                return {"results": results, "count": len(results)}
            
            elif action == 'count':
                collection = (qs.get('collection') or [None])[0]
                
                filters = None
                filters_raw = (qs.get('filters') or [None])[0]
                if filters_raw:
                    filters = json.loads(filters_raw)
                
                count = self.qdrant_handler.count(
                    filters=filters,
                    collection_name=collection
                )
                return {"count": count}
            
            elif action == 'retrieve':
                collection = (qs.get('collection') or [None])[0]
                ids_raw = (qs.get('ids') or [None])[0]
                
                if not ids_raw:
                    return {"error": "Missing 'ids' parameter"}
                
                # Parse IDs - can be comma-separated or JSON array
                try:
                    point_ids = json.loads(ids_raw)
                except (json.JSONDecodeError, ValueError):
                    point_ids = ids_raw.split(',')
                
                if not isinstance(point_ids, list):
                    return {"error": "IDs must be a JSON array or comma-separated string"}
                
                with_payload = (qs.get('with_payload') or ['true'])[0].lower() == 'true'
                with_vectors = (qs.get('with_vectors') or ['false'])[0].lower() == 'true'
                
                results = self.qdrant_handler.retrieve(
                    point_ids=point_ids,
                    collection_name=collection,
                    with_payload=with_payload,
                    with_vectors=with_vectors
                )
                return {"points": results, "count": len(results)}
            
            elif action == 'textsearch':
                # Text pattern search: scroll through collection and filter by text patterns
                collection = (qs.get('collection') or [None])[0]
                if not collection:
                    return {"error": "Missing 'collection' parameter for textsearch"}
                
                # Get search parameters
                search_field = (qs.get('field') or [None])[0]
                search_pattern = (qs.get('pattern') or [None])[0]
                search_mode = (qs.get('mode') or ['contains'])[0].lower()  # 'contains', 'startswith', 'exact', 'ilike'
                limit = int((qs.get('limit') or ['100'])[0])
                
                if not search_field or not search_pattern:
                    return {"error": "Missing 'field' or 'pattern' parameter"}
                
                # Scroll through collection and apply text filter
                all_points = []
                offset = 0
                max_scroll = 10000  # Safety limit
                
                while len(all_points) < limit and offset < max_scroll:
                    batch = self.qdrant_handler.scroll_points(
                        collection_name=collection,
                        limit=min(100, limit - len(all_points)),
                        offset=offset,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    if not batch.get('points'):
                        break
                    
                    # Filter points by text pattern
                    for point in batch['points']:
                        if self._matches_text_pattern(point, search_field, search_pattern, search_mode):
                            all_points.append(point)
                            if len(all_points) >= limit:
                                break
                    
                    offset += len(batch['points'])
                    if len(batch['points']) < 100:  # No more points
                        break
                
                return {
                    "points": all_points,
                    "count": len(all_points),
                    "limit": limit,
                    "search_field": search_field,
                    "search_pattern": search_pattern,
                    "search_mode": search_mode
                }
            
            else:
                return {"error": f"Unknown action: {action}. Valid: collections, info, scroll, search, count, retrieve, textsearch"}
                
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in parameters: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def handle_embeddings(self, qs: Dict, embedding_generator) -> Dict:
        """Handle embedding generation requests.
        
        Query parameters:
            text: Text to embed (required)
            
        Returns:
            Dict with 'vector' key containing the embedding
        """
        try:
            text = (qs.get('text') or [None])[0]
            if not text:
                return {"error": "Missing 'text' parameter"}
            
            vector = embedding_generator.embed_text(text)
            return {
                "text": text,
                "vector": vector,
                "dimension": len(vector)
            }
        except Exception as e:
            return {"error": f"Failed to generate embedding: {str(e)}"}
    
    def _matches_text_pattern(self, point: Dict, field: str, pattern: str, mode: str = 'contains') -> bool:
        """Check if a point matches a text pattern in a specified field.
        
        Args:
            point: Qdrant point with 'payload' dict
            field: Field name in payload to search
            pattern: Text pattern to match
            mode: Match mode - 'contains', 'startswith', 'exact', 'ilike'
            
        Returns:
            True if point matches the pattern
        """
        try:
            if not point.get('payload'):
                return False
            
            value = point['payload'].get(field)
            if value is None:
                return False
            
            value_str = str(value).lower()
            pattern_lower = pattern.lower()
            
            if mode == 'exact':
                return value_str == pattern_lower
            elif mode == 'startswith':
                return value_str.startswith(pattern_lower)
            elif mode == 'ilike':
                # SQL ILIKE pattern matching: % is wildcard
                pattern_no_wildcards = pattern_lower.replace('%', '')
                return pattern_no_wildcards in value_str
            else:  # 'contains' (default)
                return pattern_lower in value_str
        except Exception:
            return False

    def _matches_all_patterns(self, point: Dict, pattern_filters: Dict) -> bool:
        """Check if a point matches all pattern filters.
        
        Args:
            point: Qdrant point with 'payload' dict
            pattern_filters: Dict of field->pattern to match
            
        Returns:
            True if point matches all patterns
        """
        if not point.get('payload'):
            return False
        
        for field, pattern in pattern_filters.items():
            value = point['payload'].get(field)
            if value is None:
                return False
            
            value_str = str(value).lower()
            pattern_str = str(pattern).lower()
            
            # Special handling for numeric/price fields (tarif)
            if field == 'tarif':
                # Try to normalize decimal numbers by removing trailing zeros
                try:
                    # Convert to float and back to string to normalize
                    value_normalized = str(float(value_str)).rstrip('0').rstrip('.')
                    pattern_normalized = str(float(pattern_str)).rstrip('0').rstrip('.')
                    
                    # Check if pattern is contained in normalized value
                    if pattern_normalized in value_normalized:
                        continue
                except (ValueError, AttributeError):
                    pass
            
            # Use contains matching for all pattern filters
            if pattern_str not in value_str:
                return False
        
        return True
    def _combined_search(self, collection: str, query: str, pattern_filters: Dict, 
                        exact_filters: Dict, limit: int, with_payload: bool, 
                        with_vectors: bool) -> Dict:
        """Combine vector search with filter matching.
        
        Performs both semantic search and filter-based search, then returns
        products that appear in both result sets (intersection).
        
        Args:
            collection: Collection name
            query: Search query text for semantic search
            pattern_filters: Pattern filters (contains matching)
            exact_filters: Exact filters
            limit: Max results
            with_payload: Include payload
            with_vectors: Include vectors
            
        Returns:
            Dict with merged results
        """
        # Step 1: Get embedding for semantic search
        try:
            # Import and use the embedding generator
            from src.embeddings import EmbeddingGenerator
            embedding_gen = EmbeddingGenerator()
            vector = embedding_gen.embed_text(query)
            
            # Step 2: Perform vector search
            vector_results = self.qdrant_handler.search(
                query_vector=vector,
                limit=limit * 2,  # Get more results for intersection
                score_threshold=None,
                filters=exact_filters if exact_filters else None,
                collection_name=collection,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            # Step 3: If we have pattern filters, filter the vector results
            if pattern_filters:
                filtered_results = []
                for point in vector_results:
                    if self._matches_all_patterns(point, pattern_filters):
                        filtered_results.append(point)
                vector_results = filtered_results
            
            # Limit to requested number
            final_results = vector_results[:limit]
            
            return {
                "points": final_results,
                "count": len(final_results),
                "next_offset": None,
                "search_type": "combined"
            }
            
        except Exception as e:
            # If embedding fails, fall back to filter-only search
            return {
                "error": f"Combined search failed: {str(e)}",
                "points": [],
                "count": 0
            }