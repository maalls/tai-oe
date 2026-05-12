"""Qdrant query operations (search, scroll, count, retrieve)."""

from typing import Dict, Optional, List, Union

try:
    from qdrant_client import QdrantClient
except ImportError:
    raise ImportError("Missing dependency: qdrant-client. Install with: pip install qdrant-client")

from src.controller.qdrant_filter import build_filter


class QdrantQueryOps:
    """Encapsulates Qdrant query operations."""
    
    def __init__(self, client: QdrantClient, default_collection: str):
        """Initialize query operations.
        
        Args:
            client: QdrantClient instance
            default_collection: Default collection name to use
        """
        self.client = client
        self.default_collection = default_collection
    
    def scroll_points(
        self,
        limit: int = 100,
        offset: Optional[str] = None,
        filters: Optional[Dict] = None,
        collection_name: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> Dict:
        """Scroll through collection points with pagination.
        
        Args:
            limit: Maximum number of points to return (default: 100, max: 1000)
            offset: Pagination offset (opaque string from previous response)
            filters: Optional metadata filters
            collection_name: Collection name (uses default if None)
            with_payload: Include payload in results
            with_vectors: Include vectors in results
            
        Returns:
            Dict with 'points' list and 'next_offset' for pagination
        """
        collection = collection_name or self.default_collection
        limit = max(1, min(limit, 1000))
        
        try:
            qdrant_filter = build_filter(filters) if filters else None
            
            points, next_offset = self.client.scroll(
                collection_name=collection,
                scroll_filter=qdrant_filter,
                limit=limit,
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            # Format results
            result_points = []
            for point in points:
                p = {'id': str(point.id)}
                if with_payload and point.payload:
                    p['payload'] = point.payload
                if with_vectors and point.vector:
                    p['vector'] = point.vector
                result_points.append(p)
            
            return {
                'points': result_points,
                'next_offset': next_offset,
                'count': len(result_points)
            }
            
        except Exception as e:
            print(f"[QdrantQueryOps] Error scrolling points: {e}")
            return {'points': [], 'next_offset': None, 'count': 0, 'error': str(e)}
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
        collection_name: Optional[str] = None,
        score_threshold: Optional[float] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict]:
        """Vector similarity search.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum results (default: 10)
            filters: Optional metadata filters
            collection_name: Collection name (uses default if None)
            score_threshold: Minimum similarity score
            with_payload: Include payload in results
            with_vectors: Include vectors in results
            
        Returns:
            List of search results with score, id, payload
        """
        collection = collection_name or self.default_collection
        limit = max(1, min(limit, 1000))
        
        try:
            qdrant_filter = build_filter(filters) if filters else None
            
            search_params = {}
            if score_threshold is not None:
                search_params['score_threshold'] = score_threshold
            
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=with_payload,
                with_vectors=with_vectors,
                **search_params
            )
            
            # Format results
            formatted = []
            for result in results:
                r = {
                    'id': str(result.id),
                    'score': float(result.score)
                }
                if with_payload and result.payload:
                    r['payload'] = result.payload
                if with_vectors and result.vector:
                    r['vector'] = result.vector
                formatted.append(r)
            
            return formatted
            
        except Exception as e:
            print(f"[QdrantQueryOps] Error searching: {e}")
            return []
    
    def count(self, filters: Optional[Dict] = None, collection_name: Optional[str] = None) -> int:
        """Count points matching filters.
        
        Args:
            filters: Optional metadata filters
            collection_name: Collection name (uses default if None)
            
        Returns:
            Count of matching points
        """
        collection = collection_name or self.default_collection
        
        try:
            qdrant_filter = build_filter(filters) if filters else None
            result = self.client.count(
                collection_name=collection,
                count_filter=qdrant_filter,
                exact=True
            )
            return result.count
        except Exception as e:
            print(f"[QdrantQueryOps] Error counting: {e}")
            return 0
    
    def retrieve(
        self,
        point_ids: List[Union[str, int]],
        collection_name: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict]:
        """Retrieve specific points by ID.
        
        Args:
            point_ids: List of point IDs
            collection_name: Collection name (uses default if None)
            with_payload: Include payload
            with_vectors: Include vectors
            
        Returns:
            List of points
        """
        collection = collection_name or self.default_collection
        
        try:
            # Convert string IDs to integers if needed
            ids = []
            for pid in point_ids:
                if isinstance(pid, str):
                    try:
                        ids.append(int(pid))
                    except ValueError:
                        ids.append(pid)
                else:
                    ids.append(pid)
            
            points = self.client.retrieve(
                collection_name=collection,
                ids=ids,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            # Format results
            result = []
            for point in points:
                p = {'id': str(point.id)}
                if with_payload and point.payload:
                    p['payload'] = point.payload
                if with_vectors and point.vector:
                    p['vector'] = point.vector
                result.append(p)
            
            return result
            
        except Exception as e:
            print(f"[QdrantQueryOps] Error retrieving points: {e}")
            return []
