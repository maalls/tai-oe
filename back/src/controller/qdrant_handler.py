"""Qdrant vector database handler."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

try:
    import yaml
except ImportError:
    raise ImportError("Missing dependency: PyYAML. Install with: pip install PyYAML")

try:
    from qdrant_client import QdrantClient
except ImportError:
    raise ImportError("Missing dependency: qdrant-client. Install with: pip install qdrant-client")

from src.controller.qdrant_query_ops import QdrantQueryOps


class QdrantHandler:
    """Handles Qdrant vector database connections and queries."""

    def upsert_point(self, point_id, vector, payload, collection_name: Optional[str] = None):
        """Insert or update a single point in Qdrant."""
        from qdrant_client.models import PointStruct
        collection = collection_name or self.collection_name
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        try:
            self.client.upsert(collection_name=collection, points=[point])
            print(f"[QdrantHandler] ✓ Upserted point {point_id}")
            return True
        except Exception as e:
            print(f"[QdrantHandler] Error upserting point: {e}")
            return False
    def __init__(self, config_path: Optional[str] = None, url: Optional[str] = None, collection_name: Optional[str] = None):
        """Initialize Qdrant handler with configuration.
        
        Args:
            config_path: Path to YAML config file. If None, uses default 'config.yml'
            url: Direct URL override (takes precedence over config)
            collection_name: Collection name override
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()
        self.qdrant_config = self._get_qdrant_config()
        
        # Allow direct overrides
        env_url = os.getenv('QDRANT_URL')
        env_collection = os.getenv('QDRANT_COLLECTION')
        self.url = url or env_url or self.qdrant_config.get('url', '/rkllm/qdrant_storage')
        self.collection_name = (
            collection_name
            or env_collection
            or self.qdrant_config.get('collection_name', 'electric_parts')
        )
        self.timeout = self.qdrant_config.get('timeout', 30)
        
        self._client = None
        self._query_ops = None
    
    def _find_config(self) -> str:
        """Find config.yml in standard locations."""
        current_dir = Path(__file__).parent.parent.parent
        config_candidates = [
            current_dir / 'config.yml',
            Path.cwd() / 'config.yml',
            Path.cwd() / 'back' / 'config.yml',
        ]
        
        for candidate in config_candidates:
            if candidate.exists():
                return str(candidate)
        
        # Return default path even if not found (will handle missing config gracefully)
        return str(current_dir / 'config.yml')
    
    def _load_config(self) -> dict:
        """Load YAML configuration file."""
        if not os.path.exists(self.config_path):
            print(f"[QdrantHandler] Config file not found: {self.config_path}, using defaults")
            return {}
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        
        return config
    
    def _get_qdrant_config(self) -> dict:
        """Extract Qdrant configuration from config."""
        return self.config.get("qdrant", {})
    
    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client (lazy initialization)."""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self) -> QdrantClient:
        """Create a new Qdrant client."""
        # Determine if URL is HTTP remote or local file path
        if self.url.startswith('http://') or self.url.startswith('https://'):
            print(f"[QdrantHandler] Connecting to remote Qdrant: {self.url}")
            return QdrantClient(url=self.url, timeout=self.timeout)
        else:
            # File-based storage (persistent)
            print(f"[QdrantHandler] Using file-based storage: {self.url}")
            return QdrantClient(path=self.url)
    
    @property
    def query_ops(self) -> QdrantQueryOps:
        """Get or create query operations handler."""
        if self._query_ops is None:
            self._query_ops = QdrantQueryOps(self.client, self.collection_name)
        return self._query_ops
    
    def test_connection(self) -> bool:
        """Test Qdrant connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            print(f"[QdrantHandler] Connection test failed: {e}")
            return False
    
    def get_collections(self) -> List[str]:
        """Get list of all collection names.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            print(f"[QdrantHandler] Error getting collections: {e}")
            return []
    
    def get_collection_info(self, collection_name: Optional[str] = None) -> Optional[Dict]:
        """Get collection information and statistics.
        
        Args:
            collection_name: Collection name (uses default if None)
            
        Returns:
            Dictionary with collection info or None on error
        """
        collection = collection_name or self.collection_name
        try:
            info = self.client.get_collection(collection)
            
            # Extract vector size from config - try multiple possible locations
            vector_size = None
            try:
                if hasattr(info, 'config') and hasattr(info.config, 'params'):
                    if hasattr(info.config.params, 'vectors'):
                        if hasattr(info.config.params.vectors, 'size'):
                            vector_size = info.config.params.vectors.size
                        elif hasattr(info.config.params.vectors, '__iter__'):
                            # If vectors is iterable, get first size
                            vectors_list = list(info.config.params.vectors)
                            if vectors_list and hasattr(vectors_list[0], 'size'):
                                vector_size = vectors_list[0].size
            except Exception:
                pass  # Fall back to None if we can't extract vector_size
            
            # Build response with available attributes
            result = {
                'name': collection,
                'points_count': info.points_count,
                'indexed_vectors_count': info.indexed_vectors_count,
                'status': str(info.status),
                'optimizer_status': str(info.optimizer_status),
                'vector_size': vector_size,
            }
            
            # Add vectors_count if available
            if hasattr(info, 'vectors_count'):
                result['vectors_count'] = info.vectors_count
            
            return result
        except Exception as e:
            print(f"[QdrantHandler] Error getting collection info for '{collection}': {e}")
            return None
    
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
        
        Delegates to QdrantQueryOps.
        """
        return self.query_ops.scroll_points(
            limit=limit,
            offset=offset,
            filters=filters,
            collection_name=collection_name,
            with_payload=with_payload,
            with_vectors=with_vectors
        )
    
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
        
        Delegates to QdrantQueryOps.
        """
        return self.query_ops.search(
            query_vector=query_vector,
            limit=limit,
            filters=filters,
            collection_name=collection_name,
            score_threshold=score_threshold,
            with_payload=with_payload,
            with_vectors=with_vectors
        )
    
    def count(self, filters: Optional[Dict] = None, collection_name: Optional[str] = None) -> int:
        """Count points matching filters.
        
        Delegates to QdrantQueryOps.
        """
        return self.query_ops.count(filters=filters, collection_name=collection_name)
    
    def retrieve(
        self,
        point_ids: List[Union[str, int]],
        collection_name: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict]:
        """Retrieve specific points by ID.
        
        Delegates to QdrantQueryOps.
        """
        return self.query_ops.retrieve(
            point_ids=point_ids,
            collection_name=collection_name,
            with_payload=with_payload,
            with_vectors=with_vectors
        )


# Singleton instance for convenience
_qdrant_handler_instance: Optional[QdrantHandler] = None


def get_qdrant_handler(
    config_path: Optional[str] = None,
    url: Optional[str] = None,
    collection_name: Optional[str] = None
) -> QdrantHandler:
    """Get or create a singleton QdrantHandler instance.
    
    Args:
        config_path: Optional path to config file
        url: Optional URL override
        collection_name: Optional collection name override
        
    Returns:
        QdrantHandler instance
    """
    global _qdrant_handler_instance
    if _qdrant_handler_instance is None:
        _qdrant_handler_instance = QdrantHandler(config_path, url, collection_name)
    return _qdrant_handler_instance
