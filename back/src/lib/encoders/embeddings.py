"""Embedding generation using sentence-transformers."""

import os
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers (lazy initialization)."""
    
    def __init__(self, model: str = None):
        """Initialize embedding generator (deferred model loading).
        
        Args:
            model: Model name (default: from EMBEDDING_MODEL env var or all-MiniLM-L6-v2)
        """
        if model is None:
            model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        
        self.model_name = model
        self.device = os.getenv('EMBEDDING_DEVICE', 'cpu')
        self.model = None
        self.vector_size = 384  # Default for all-MiniLM-L6-v2
        print(f"[EmbeddingGenerator] Will load '{model}' on first use (device: '{self.device}')")
    
    def _ensure_model_loaded(self):
        """Lazy load model on first embedding request."""
        if self.model is not None:
            return
        
        print(f"[EmbeddingGenerator] Loading model '{self.model_name}' on device '{self.device}'...")
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.vector_size = self.model.get_sentence_embedding_dimension()
            print(f"[EmbeddingGenerator] ✓ Loaded {self.model_name} (dimension: {self.vector_size})")
        except Exception as e:
            print(f"[EmbeddingGenerator] ✗ Failed to load model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        self._ensure_model_loaded()  # Lazy load on first use
        
        try:
            if not text or not text.strip():
                # Return zero vector if text is empty
                return [0.0] * self.vector_size
            
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"[EmbeddingGenerator] Error embedding text: {e}")
            return [0.0] * self.vector_size
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        self._ensure_model_loaded()  # Ensure model is loaded
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"[EmbeddingGenerator] Error embedding batch: {e}")
            return [[0.0] * self.vector_size for _ in texts]
