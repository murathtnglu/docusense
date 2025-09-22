# DocuSense
*A Production-Grade Retrieval-Augmented Generation (RAG) System*

DocuSense is an intelligent document Q&A system that combines **vector search** and **keyword search** to deliver accurate, context-aware answers powered by **Large Language Models (LLMs)**.  

Users can upload documents (PDF, text, URLs), which are parsed, chunked, embedded, and stored in a **PostgreSQL + pgvector** database. Queries are processed through a **hybrid retrieval pipeline** and answered with citations from the original sources.

---

## Features
-  **Multi-format ingestion** (PDF, TXT, Markdown, Web URLs)  
-  **Smart chunking** with overlap for better context  
-  **Hybrid retrieval** (Vector similarity + BM25 keyword search)  
-  **LLM integration** with OpenAI and Ollama (local inference)  
-  **Citations & confidence scores** included in answers  
-  **Collection management** for organizing documents  
-  **Async workers** for background processing with Redis + Celery  

---

## Tech Stack

**Frontend**  
- Next.js (TypeScript, React)  
- Tailwind CSS  

**Backend**  
- FastAPI (Python)  
- SQLAlchemy + pgvector (PostgreSQL)  
- Celery + Redis (background jobs)  

**ML/NLP**  
- SentenceTransformers (BAAI/bge-small-en-v1.5)  
- Hybrid retrieval (pgvector + BM25)  
- OpenAI / Ollama integration  

**Infrastructure**  
- Docker & Docker Compose  

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/murathtnglu/docusense.git
cd docusense

```
### 2. Start Services with Docker

```bash
docker-compose up -d postgres redis
```
### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate   # (On Mac/Linux)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
### 5. Access the App

- Frontend: Available at http://localhost:3000
- Backend: The backend API is available at http://localhost:8000/docs




