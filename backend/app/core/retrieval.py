from typing import List, Dict, Tuple, Optional
import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from app.models.database import Chunk, Document, Collection

class HybridRetriever:
    """Hybrid retrieval using both vector and keyword search"""
    
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        self.bm25_index = None
        self.chunk_ids = []
    
    def build_bm25_index(self, chunks: List[Chunk]):
        """Build BM25 index for keyword search"""
        # Tokenize chunks for BM25
        tokenized_chunks = [
            self._tokenize(chunk.text.lower()) 
            for chunk in chunks
        ]
        self.bm25_index = BM25Okapi(tokenized_chunks)
        self.chunk_ids = [chunk.id for chunk in chunks]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()
    
    def vector_search(
        self, 
        db: Session,
        query_embedding: np.ndarray,
        collection_id: int,
        top_k: int = 20
    ) -> List[Tuple[int, float]]:
        """
        Perform vector similarity search using pgvector
        Returns list of (chunk_id, score) tuples
        """
        # Convert embedding to list for PostgreSQL
        embedding_list = query_embedding.tolist()
        
        # Use pgvector's <-> operator for cosine distance
        query = text("""
            SELECT c.id, 
                   (1 - (c.embedding <-> :embedding)) as similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.collection_id = :collection_id
            ORDER BY c.embedding <-> :embedding
            LIMIT :limit
        """)
        
        results = db.execute(
            query,
            {
                "embedding": str(embedding_list),
                "collection_id": collection_id,
                "limit": top_k
            }
        ).fetchall()
        
        return [(row[0], row[1]) for row in results]
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 20
    ) -> List[Tuple[int, float]]:
        """
        Perform BM25 keyword search
        Returns list of (chunk_id, score) tuples
        """
        if not self.bm25_index:
            return []
        
        tokenized_query = self._tokenize(query.lower())
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append((self.chunk_ids[idx], float(scores[idx])))
        
        return results
    
    def hybrid_search(
        self,
        db: Session,
        query: str,
        collection_id: int,
        top_k: int = 10,
        vector_weight: float = 0.7
    ) -> List[Dict]:
        """
        Combine vector and keyword search using reciprocal rank fusion
        """
        # Get query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Perform both searches
        vector_results = self.vector_search(db, query_embedding, collection_id, top_k * 2)
        keyword_results = self.keyword_search(query, top_k * 2)
        
        # Reciprocal Rank Fusion
        k = 60  # RRF parameter
        scores = {}
        
        # Add vector search scores
        for rank, (chunk_id, score) in enumerate(vector_results):
            scores[chunk_id] = scores.get(chunk_id, 0) + (
                vector_weight / (k + rank + 1)
            )
        
        # Add keyword search scores  
        for rank, (chunk_id, score) in enumerate(keyword_results):
            if chunk_id in [c[0] for c in vector_results]:  # Only if in collection
                scores[chunk_id] = scores.get(chunk_id, 0) + (
                    (1 - vector_weight) / (k + rank + 1)
                )
        
        # Sort by combined score
        sorted_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Fetch chunk details
        chunk_ids = [chunk_id for chunk_id, _ in sorted_chunks]
        chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        
        # Create result with scores
        chunk_dict = {chunk.id: chunk for chunk in chunks}
        results = []
        for chunk_id, score in sorted_chunks:
            if chunk_id in chunk_dict:
                chunk = chunk_dict[chunk_id]
                results.append({
                    'chunk': chunk,
                    'score': score,
                    'text': chunk.text,
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index
                })
        
        return results