from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import os
from functools import lru_cache

class EmbeddingService:
    """Handle text embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", 
            "BAAI/bge-small-en-v1.5"
        )
        self.model = self._load_model()
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    @lru_cache(maxsize=1)
    def _load_model(self) -> SentenceTransformer:
        """Load and cache the embedding model"""
        print(f"Loading embedding model: {self.model_name}")
        return SentenceTransformer(self.model_name)
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text or list of texts
        Returns numpy array of embeddings
        """
        if isinstance(text, str):
            text = [text]
        
        # Generate embeddings
        embeddings = self.model.encode(
            text,
            normalize_embeddings=True,  # Normalize for cosine similarity
            show_progress_bar=False
        )
        
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a search query (might use different processing in future)
        """
        # For BGE models, add instruction prefix
        if "bge" in self.model_name.lower():
            query = f"Represent this sentence for searching relevant passages: {query}"
        
        return self.embed_text(query)[0]
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed texts in batches for efficiency
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embed_text(batch)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)