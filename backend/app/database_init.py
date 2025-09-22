import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Base, engine
from sqlalchemy import text

def init_database():
    """Initialize database with pgvector extension and create tables"""
    
    # Create pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
    print("✅ Tables created: collections, documents, chunks, queries, etc.")

if __name__ == "__main__":
    init_database()