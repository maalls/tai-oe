"""Qdrant Vector Database client wrapper."""

import os
import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue
)
from embeddings import EmbeddingGenerator
from vectordb_filters import build_conditions, format_result


class VectorDBClient:
    """Qdrant client for semantic search with metadata filtering."""
    
    def __init__(
        self,
        url: str = None,
        embedding_model: str = None,
        collection_name: str = "electric_parts",
        timeout: int = 30
    ):
        """Initialize Qdrant client.
        
        Args:
            url: Qdrant server URL or file path (default: QDRANT_URL env var or /rkllm/qdrant_storage)
            embedding_model: Embedding model (default: EMBEDDING_MODEL env var)
            collection_name: Collection name (default: electric_parts)
            timeout: Request timeout in seconds (default: 30)
        """
        if url is None:
            url = os.getenv('QDRANT_URL', '/rkllm/qdrant_storage')
        
        self.url = url
        self.collection_name = collection_name
        self.embedding_gen = EmbeddingGenerator(model=embedding_model)
        self.vector_size = self.embedding_gen.vector_size
        # Error tracking for more explicit server responses
        self.last_error: Optional[str] = None
        self.last_error_trace: Optional[str] = None
        
        # Determine if URL is HTTP remote or local file path
        if url.startswith('http://') or url.startswith('https://'):
            print(f"[VectorDBClient] Connecting to remote Qdrant: {url}")
            try:
                self.client = QdrantClient(url=url, timeout=timeout)
                print(f"[VectorDBClient] ✓ Connected to remote Qdrant")
            except Exception as e:
                print(f"[VectorDBClient] ✗ Connection failed: {e}")
                raise
        else:
            # File-based storage (persistent)
            print(f"[VectorDBClient] Using persistent file-based storage: {url}")
            self.client = QdrantClient(path=url)
            print(f"[VectorDBClient] ✓ File-based client ready")
    
    def health_check(self) -> bool:
        """Check if Qdrant server is healthy."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            print(f"[VectorDBClient] Health check failed: {e}")
            return False
    
    def create_collection(self) -> bool:
        """Create or verify collection exists."""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name in collection_names:
                print(f"[VectorDBClient] Collection '{self.collection_name}' exists")
                return True
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"[VectorDBClient] ✓ Created collection '{self.collection_name}'")
            return True
            
        except Exception as e:
            print(f"[VectorDBClient] Error creating collection: {e}")
            return False

    def upsert_part(self, part: Dict) -> bool:
        """Insert or update a single part."""
        try:
            part_id = part.get('id') or part.get('part_id')
            if not part_id:
                msg = "no id/part_id provided"
                print(f"[VectorDBClient] Error: {msg}")
                self.last_error = msg
                self.last_error_trace = None
                return False
            
            text = f"{part.get('part_name', '')} {part.get('description', '')}"
            vector = self.embedding_gen.embed_text(text)

            payload = {
                'part_id': part_id,
                'part_name': part.get('part_name', ''),
                'part_type': part.get('part_type', ''),
                'description': part.get('description', ''),
                'vendor': part.get('vendor', ''),
                'price': float(part.get('price', 0)),
                'in_stock': bool(part.get('in_stock', True)),
                'tags': part.get('tags', []),
                'tenant_id': part.get('tenant_id', 'default'),
                'project_id': part.get('project_id', 'electronics_catalog'),
                'doc_type': 'product',
                'source': part.get('source', 'inventory'),
            }

            point_id = hash(payload['part_id']) % (2**31)
            point = PointStruct(id=point_id, vector=vector, payload=payload)
            
            self.client.upsert(collection_name=self.collection_name, points=[point])
            print(f"[VectorDBClient] ✓ Upserted part {part_id} (dim: {len(vector)})")
            return True
        except Exception as e:
            print(f"[VectorDBClient] Error upserting part: {e}")
            import traceback
            tb = traceback.format_exc()
            print(tb)
            self.last_error = str(e)
            self.last_error_trace = tb
            return False

    def delete_part(self, part_id: str) -> bool:
        """Delete a part by part_id."""
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key='part_id',
                            match=MatchValue(value=part_id)
                        )
                    ]
                ),
                limit=1
            )

            if not points:
                print(f"[VectorDBClient] Part {part_id} not found for delete")
                return False

            point = points[0]
            self.client.delete(collection_name=self.collection_name, points_selector=[point.id])
            print(f"[VectorDBClient] ✓ Deleted part {part_id}")
            return True
        except Exception as e:
            print(f"[VectorDBClient] Error deleting part: {e}")
            return False

    def count_parts(self, filters: Optional[Dict] = None) -> int:
        """Count total parts matching filters."""
        try:
            qdrant_filter = build_conditions(filters)
            result = self.client.count(
                collection_name=self.collection_name,
                count_filter=qdrant_filter,
                exact=True
            )
            return result.count
        except Exception as e:
            print(f"[VectorDBClient] Error counting parts: {e}")
            return 0

    def _scroll_all(self, qdrant_filter, max_records: int) -> List:
        """Scroll through Qdrant results until max_records or end."""
        all_points = []
        next_page_offset = None
        
        while len(all_points) < max_records:
            points, next_page_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=qdrant_filter,
                limit=min(100, max_records - len(all_points)),
                offset=next_page_offset,
                with_payload=True,
                with_vectors=False
            )
            if not points:
                break
            all_points.extend(points)
            if next_page_offset is None:
                break
        return all_points
    
    def list_parts(self, limit: int = 50, offset: int = 0, filters: Optional[Dict] = None) -> List[Dict]:
        """List parts with optional filters using numeric offset pagination."""
        try:
            qdrant_filter = build_conditions(filters)
            all_points = self._scroll_all(qdrant_filter, offset + limit)
            sliced_points = all_points[offset:offset + limit]
            return [format_result(p.payload, None) for p in sliced_points]
        except Exception as e:
            print(f"[VectorDBClient] Error listing parts: {e}")
            return []
    
    def query_similar(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Semantic search with optional metadata filtering.
        
        Args:
            query: Search query string
            filters: Optional metadata filters (price_min, price_max, vendor, part_type, in_stock, tenant_id)
            limit: Max results (default: 10)
            
        Returns:
            List of matching parts with metadata
        """
        try:
            # Generate embedding for query
            query_vector = self.embedding_gen.embed_text(query)
            
            # Build Qdrant filter
            qdrant_filter = build_conditions(filters)
            
            # Perform search
            start_time = time.time()
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            query_time_ms = int((time.time() - start_time) * 1000)
            
            # Format results
            results = [format_result(sp.payload, float(sp.score)) for sp in search_results]
            print(f"[VectorDBClient] Query '{query[:50]}' found {len(results)} results in {query_time_ms}ms")
            return results
            
        except Exception as e:
            print(f"[VectorDBClient] Error querying: {e}")
            return []
    
    def update_part(self, part_id: str, updates: Dict) -> bool:
        """Update part metadata."""
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key='part_id',
                            match=MatchValue(value=part_id)
                        )
                    ]
                ),
                limit=1
            )
            
            if not points:
                print(f"[VectorDBClient] Part {part_id} not found")
                return False
            
            point = points[0]
            payload = {**point.payload, **updates}
            
            self.client.update_points(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=payload
                    )
                ]
            )
            
            print(f"[VectorDBClient] ✓ Updated part {part_id}")
            return True
            
        except Exception as e:
            print(f"[VectorDBClient] Error updating part: {e}")
            return False
    
    def delete_collection(self) -> bool:
        """Delete entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"[VectorDBClient] ✓ Deleted collection '{self.collection_name}'")
            return True
        except Exception as e:
            print(f"[VectorDBClient] Error deleting collection: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict]:
        """Get collection statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'status': str(info.status)
            }
        except Exception as e:
            print(f"[VectorDBClient] Error getting info: {e}")
            return None
