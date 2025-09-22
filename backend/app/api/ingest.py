from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import uuid
import os
import shutil
from datetime import datetime

from app.models.database import SessionLocal, Document, Chunk, IngestJob, Collection
from app.core.parsers import DocumentParser
from app.core.chunking import DocumentChunker
from app.core.embeddings import EmbeddingService
from app.api.collections import get_db

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

# Global instances
chunker = DocumentChunker()
embedding_service = EmbeddingService()
parser = DocumentParser()

class IngestRequest(BaseModel):
    collection_id: int
    url: Optional[str] = None
    text: Optional[str] = None
    title: str

class IngestResponse(BaseModel):
    job_id: str
    status: str
    message: str

def process_document(job_id: str, document_id: int, content: str, source_type: str):
    """Background task to process document"""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(IngestJob).filter(IngestJob.id == job_id).first()
        job.status = "processing"
        job.progress = 10
        db.commit()
        
        # Parse document based on type
        if source_type == "url":
            parsed = parser.parse_url(content)
        elif source_type == "pdf":
            parsed = parser.parse_pdf(content)
        elif source_type == "markdown":
            parsed = parser.parse_markdown(content)
        else:
            parsed = parser.parse_text(content)
        
        job.progress = 30
        db.commit()
        
        # Chunk the document
        chunks_data = chunker.chunk_text(parsed["text"])
        
        job.progress = 50
        db.commit()
        
        # Generate embeddings in batches
        texts = [chunk["text"] for chunk in chunks_data]
        embeddings = embedding_service.embed_batch(texts, batch_size=32)
        
        job.progress = 80
        db.commit()
        
        # Store chunks in database
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            chunk = Chunk(
                document_id=document_id,
                text=chunk_data["text"],
                token_count=chunk_data["token_count"],
                chunk_index=chunk_data["chunk_index"],
                start_char=chunk_data.get("start_char", 0),
                end_char=chunk_data.get("end_char", len(chunk_data["text"])),
                embedding=embedding.tolist(),
                meta_data=chunk_data.get("meta_data", {})
            )
            db.add(chunk)
        
        db.commit()
        
        # Update job as completed
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.utcnow()
        db.commit()
        
        print(f"✅ Processed document {document_id}: {len(chunks_data)} chunks")
        
    except Exception as e:
        print(f"❌ Error processing document: {str(e)}")
        job = db.query(IngestJob).filter(IngestJob.id == job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()

@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    collection_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and ingest a document"""
    # Verify collection exists
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse to get text for checksum
        if file.filename.endswith('.pdf'):
            parsed = parser.parse_pdf(temp_path)
            source_type = "pdf"
        else:
            with open(temp_path, 'r',encoding='utf-8') as f:
                content = f.read()
            parsed = parser.parse_text(content)
            source_type = "text"
        
        # Check for duplicates
        checksum = parser.calculate_checksum(parsed["text"])
        existing = db.query(Document).filter(Document.checksum == checksum).first()
        if existing:
            raise HTTPException(status_code=400, detail="Document already exists")
        
        # Create document record
        document = Document(
            collection_id=collection_id,
            title=file.filename,
            source_type=source_type,
            checksum=checksum,
            meta_data=parsed.get("meta_data", {})
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Create job
        job_id = str(uuid.uuid4())
        job = IngestJob(
            id=job_id,
            collection_id=collection_id,
            document_id=document.id,
            status="pending"
        )
        db.add(job)
        db.commit()
        
        # Start background processing
        background_tasks.add_task(
            process_document,
            job_id,
            document.id,
            temp_path if source_type == "pdf" else parsed["text"],
            source_type
        )
        
        return IngestResponse(
            job_id=job_id,
            status="pending",
            message=f"Document '{file.filename}' queued for processing"
        )
        
    finally:
        # Cleanup temp file later
        if os.path.exists(temp_path) and source_type != "pdf":
            os.remove(temp_path)

@router.post("/url", response_model=IngestResponse)
async def ingest_url(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Ingest content from URL"""
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Verify collection exists
    collection = db.query(Collection).filter(Collection.id == request.collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Create document record
    document = Document(
        collection_id=request.collection_id,
        title=request.title,
        source_type="url",
        source_url=request.url
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Create job
    job_id = str(uuid.uuid4())
    job = IngestJob(
        id=job_id,
        collection_id=request.collection_id,
        document_id=document.id,
        status="pending"
    )
    db.add(job)
    db.commit()
    
    # Start background processing
    background_tasks.add_task(
        process_document,
        job_id,
        document.id,
        request.url,
        "url"
    )
    
    return IngestResponse(
        job_id=job_id,
        status="pending",
        message=f"URL '{request.url}' queued for processing"
    )

@router.get("/status/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Check ingestion job status"""
    job = db.query(IngestJob).filter(IngestJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }