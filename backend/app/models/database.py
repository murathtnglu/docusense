from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://docusense:docusense@localhost:5432/docusense")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    settings = Column(JSON, default={})
    
    documents = relationship("Document", back_populates="collection")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"))
    title = Column(String(500), nullable=False)
    source_type = Column(String(50))  # pdf, url, markdown
    source_url = Column(Text)
    checksum = Column(String(64))  # For deduplication
    meta_data = Column(JSON, default={})  # CHANGED: renamed from metadata
    created_at = Column(DateTime, default=func.now())
    
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    text = Column(Text, nullable=False)
    token_count = Column(Integer)
    page_number = Column(Integer)
    chunk_index = Column(Integer)  # Order within document
    start_char = Column(Integer)
    end_char = Column(Integer)
    embedding = Column(Vector(384))  # Adjust dimension based on model
    meta_data = Column(JSON, default={})  # CHANGED: renamed from metadata
    
    document = relationship("Document", back_populates="chunks")

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text)
    citations = Column(JSON)
    latency_ms = Column(Integer)
    llm_model = Column(String(100))
    retrieval_score = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    chunks_used = relationship("QueryChunk", back_populates="query")
    feedback = relationship("Feedback", back_populates="query", uselist=False)

class QueryChunk(Base):
    __tablename__ = "query_chunks"
    
    query_id = Column(Integer, ForeignKey("queries.id"), primary_key=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), primary_key=True)
    rank = Column(Integer)
    score = Column(Float)
    
    query = relationship("Query", back_populates="chunks_used")
    chunk = relationship("Chunk")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("queries.id"), unique=True)
    value = Column(Integer)  # 1 for thumbs up, -1 for thumbs down
    note = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    query = relationship("Query", back_populates="feedback")

class IngestJob(Base):
    __tablename__ = "ingest_jobs"
    
    id = Column(String(36), primary_key=True)  # UUID
    collection_id = Column(Integer, ForeignKey("collections.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    status = Column(String(50))  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)