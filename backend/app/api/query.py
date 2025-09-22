from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
import time

from app.models.database import SessionLocal, Query, QueryChunk, Chunk, Collection
from app.core.embeddings import EmbeddingService
from app.core.retrieval import HybridRetriever
from app.core.llm import LLMService
from app.api.collections import get_db

router = APIRouter(prefix="/api", tags=["query"])

# Initialize services
embedding_service = EmbeddingService()
retriever = HybridRetriever(embedding_service)
llm_service = LLMService()

class QueryRequest(BaseModel):
    question: str
    collection_id: int
    top_k: int = 10
    use_hybrid: bool = True

class QueryResponse(BaseModel):
    answer: str
    citations: List[Dict]
    confidence: float
    latency_ms: int

@router.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    """Ask a question on a collection"""
    start_time = time.time()
    
    # Verify collection exists
    collection = db.query(Collection).filter(Collection.id == request.collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Get all chunks for the collection (for BM25)
    chunks = db.query(Chunk).join(Chunk.document).filter(
        Chunk.document.has(collection_id=request.collection_id)
    ).all()
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Collection has no documents")
    
    # Build BM25 index
    retriever.build_bm25_index(chunks)
    
    # Perform retrieval
    if request.use_hybrid:
        results = retriever.hybrid_search(
            db,
            request.question,
            request.collection_id,
            top_k=request.top_k
        )
    else:
        # Just vector search
        query_embedding = embedding_service.embed_query(request.question)
        vector_results = retriever.vector_search(
            db,
            query_embedding,
            request.collection_id,
            top_k=request.top_k
        )
        # Convert to results format
        chunk_ids = [chunk_id for chunk_id, _ in vector_results]
        chunks_retrieved = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        results = [
            {
                'chunk': chunk,
                'score': score,
                'text': chunk.text,
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index
            }
            for chunk, (_, score) in zip(chunks_retrieved, vector_results)
        ]
    
    # Check answerability
    confidence = llm_service.check_answerability(request.question, results)
    
    # Change from 0.3 to 0.05
    if confidence < 0.05:  # Much lower threshold
        return QueryResponse(
            answer="I cannot find enough relevant information to answer this question.",
            citations=[],
            confidence=confidence,
            latency_ms=int((time.time() - start_time) * 1000)
        )
        
    # Generate answer
    answer_data = llm_service.generate_answer(
        request.question,
        results[:5]  # Use top 5 chunks
    )
    
    # Save query to database
    query_record = Query(
        collection_id=request.collection_id,
        question=request.question,
        answer=answer_data["answer"],
        citations=answer_data["citations"],
        latency_ms=answer_data["latency_ms"],
        llm_model=answer_data["model"],
        retrieval_score=confidence
    )
    db.add(query_record)
    db.commit()
    db.refresh(query_record)
    
    # Save chunks used
    for i, result in enumerate(results[:5]):
        query_chunk = QueryChunk(
            query_id=query_record.id,
            chunk_id=result['chunk'].id,
            rank=i + 1,
            score=result['score']
        )
        db.add(query_chunk)
    db.commit()
    
    total_latency = int((time.time() - start_time) * 1000)
    
    return QueryResponse(
        answer=answer_data["answer"],
        citations=answer_data["citations"],
        confidence=confidence,
        latency_ms=total_latency
    )

@router.post("/feedback/{query_id}")
def submit_feedback(
    query_id: int,
    value: int,  # 1 for thumbs up, -1 for thumbs down
    note: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Submit feedback for a query"""
    from app.models.database import Feedback
    
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Check if feedback already exists
    existing = db.query(Feedback).filter(Feedback.query_id == query_id).first()
    if existing:
        existing.value = value
        existing.note = note
    else:
        feedback = Feedback(
            query_id=query_id,
            value=value,
            note=note
        )
        db.add(feedback)
    
    db.commit()
    
    return {"message": "Feedback submitted successfully"}