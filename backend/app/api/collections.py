from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.models.database import SessionLocal, Collection, Document
from app.core.parsers import DocumentParser

router = APIRouter(prefix="/api/collections", tags=["collections"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class CollectionCreate(BaseModel):
    name: str
    description: str = ""

class CollectionResponse(BaseModel):
    id: int
    name: str
    description: str
    document_count: int = 0
    created_at: datetime

@router.post("/", response_model=CollectionResponse)
def create_collection(collection: CollectionCreate, db: Session = Depends(get_db)):
    """Create a new collection"""
    # Check if name already exists
    existing = db.query(Collection).filter(Collection.name == collection.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Collection name already exists")
    
    db_collection = Collection(
        name=collection.name,
        description=collection.description
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    
    return CollectionResponse(
        id=db_collection.id,
        name=db_collection.name,
        description=db_collection.description,
        document_count=0,
        created_at=db_collection.created_at
    )

@router.get("/", response_model=List[CollectionResponse])
def list_collections(db: Session = Depends(get_db)):
    """List all collections"""
    collections = db.query(Collection).all()
    
    results = []
    for col in collections:
        doc_count = db.query(Document).filter(Document.collection_id == col.id).count()
        results.append(CollectionResponse(
            id=col.id,
            name=col.name,
            description=col.description,
            document_count=doc_count,
            created_at=col.created_at
        ))
    
    return results

@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    """Get a specific collection"""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    doc_count = db.query(Document).filter(Document.collection_id == collection_id).count()
    
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        document_count=doc_count,
        created_at=collection.created_at
    )