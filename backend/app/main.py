from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import routers
from app.api import collections, ingest, query

# Load environment variables
load_dotenv()

app = FastAPI(title="DocuSense API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(collections.router)
app.include_router(ingest.router)
app.include_router(query.router)

@app.get("/")
def root():
    return {"message": "DocuSense API is running!", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/metrics")
def get_metrics():
    """Get basic metrics"""
    from app.models.database import SessionLocal, Query, Document, Collection
    
    db = SessionLocal()
    try:
        metrics = {
            "total_collections": db.query(Collection).count(),
            "total_documents": db.query(Document).count(),
            "total_queries": db.query(Query).count(),
            "avg_latency_ms": db.query(Query).with_entities(
                func.avg(Query.latency_ms)
            ).scalar() or 0
        }
        return metrics
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)