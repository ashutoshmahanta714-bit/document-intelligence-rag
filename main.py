from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import os
import shutil
import uuid
from pathlib import Path
from typing import List

from rag_engine import RAGEngine


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Document Intelligence RAG API", version="1.1.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

upload_path = Path(os.getenv("UPLOAD_DIR", "uploads")).expanduser()
UPLOAD_DIR = upload_path if upload_path.is_absolute() else BASE_DIR / upload_path
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

rag = RAGEngine()


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    question: str


@app.get("/api/status")
def api_status():
    return {"message": "Document Intelligence RAG API is running!"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document."""
    original_name = file.filename or "document"
    ext = Path(original_name).suffix.lower()
    allowed_exts = [".pdf", ".txt", ".docx", ".csv", ".md"]

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext or '(none)'} not supported. Allowed: {allowed_exts}",
        )

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{ext}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_added = rag.ingest_document(str(file_path), original_name)
        return {
            "success": True,
            "file_id": file_id,
            "filename": original_name,
            "chunks_indexed": chunks_added,
            "message": f"Successfully indexed {chunks_added} chunks from {original_name}",
        }
    except HTTPException:
        raise
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(exc)}",
        ) from exc
    finally:
        await file.close()


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the indexed documents."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = rag.query(request.question, top_k=request.top_k)
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            question=request.question,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(exc)}",
        ) from exc


@app.get("/documents")
def list_documents():
    """List all indexed documents."""
    docs = rag.list_documents()
    return {"documents": docs, "total": len(docs)}


@app.delete("/documents/{doc_name}")
def delete_document(doc_name: str):
    """Delete a document from the index."""
    success = rag.delete_document(doc_name)
    if success:
        return {"message": f"Document '{doc_name}' deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "documents_indexed": len(rag.list_documents()),
        "vector_store_size": rag.get_vector_count(),
    }


dist_dir = BASE_DIR / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
