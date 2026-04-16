from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from rag_engine import RAGEngine

app = FastAPI(title="Document Intelligence RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

rag = RAGEngine()


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    question: str


@app.get("/")
def root():
    return {"message": "Document Intelligence RAG API is running!"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document."""
    allowed_types = [
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/csv",
        "text/markdown",
    ]

    ext = Path(file.filename).suffix.lower()
    allowed_exts = [".pdf", ".txt", ".docx", ".csv", ".md"]

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not supported. Allowed: {allowed_exts}",
        )

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{ext}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        chunks_added = rag.ingest_document(str(file_path), file.filename)
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "chunks_indexed": chunks_added,
            "message": f"Successfully indexed {chunks_added} chunks from {file.filename}",
        }
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


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
