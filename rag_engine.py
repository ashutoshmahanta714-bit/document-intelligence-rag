"""
RAG Engine - Core Retrieval-Augmented Generation Logic
Uses: ChromaDB (vector store) + Sentence Transformers (embeddings) + OpenAI/Ollama (LLM)
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from openai import OpenAI


class RAGEngine:
    def __init__(
        self,
        collection_name: str = "documents",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name

        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)

        # Initialize ChromaDB (persistent local vector store)
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Initialize LLM client (OpenAI or compatible)
        self.llm_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
        )
        self.llm_model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

        # Track documents
        self._documents: Dict[str, dict] = {}

    # ─────────────────────────────────────────────
    # Document Ingestion
    # ─────────────────────────────────────────────

    def ingest_document(self, file_path: str, original_name: str) -> int:
        """Parse, chunk, embed, and store a document."""
        ext = Path(file_path).suffix.lower()

        # Parse document to text
        text = self._parse_document(file_path, ext)
        if not text.strip():
            raise ValueError("Document appears to be empty or unreadable.")

        # Split into chunks
        chunks = self._split_text(text)

        # Embed chunks
        embeddings = self.embedder.encode(chunks).tolist()

        # Store in ChromaDB
        ids = [f"{original_name}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": original_name,
                "chunk_index": i,
                "file_path": file_path,
            }
            for i in range(len(chunks))
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        # Track document
        self._documents[original_name] = {
            "name": original_name,
            "chunks": len(chunks),
            "path": file_path,
        }

        return len(chunks)

    def _parse_document(self, file_path: str, ext: str) -> str:
        """Extract text from various file types."""
        if ext == ".txt" or ext == ".md":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == ".pdf":
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += (page.extract_text() or "") + "\n"
                return text
            except ImportError:
                raise ImportError("Install pdfplumber: pip install pdfplumber")

        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                raise ImportError("Install python-docx: pip install python-docx")

        elif ext == ".csv":
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                return df.to_string(index=False)
            except ImportError:
                raise ImportError("Install pandas: pip install pandas")

        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        text = re.sub(r"\s+", " ", text).strip()
        words = text.split(" ")
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap

        return chunks

    # ─────────────────────────────────────────────
    # Query & Answer Generation
    # ─────────────────────────────────────────────

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant chunks and generate an answer."""
        if self.collection.count() == 0:
            return {
                "answer": "No documents have been indexed yet. Please upload some documents first.",
                "sources": [],
            }

        # Embed the question
        query_embedding = self.embedder.encode([question]).tolist()

        # Retrieve top-k relevant chunks
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Build context
        context = "\n\n".join(
            [f"[Source: {m['source']}, Chunk {m['chunk_index']}]\n{c}"
             for c, m in zip(chunks, metadatas)]
        )

        # Generate answer with LLM
        answer = self._generate_answer(question, context)

        # Build sources list
        sources = [
            {
                "source": m["source"],
                "chunk_index": m["chunk_index"],
                "relevance_score": round(1 - d, 4),
                "excerpt": c[:200] + "..." if len(c) > 200 else c,
            }
            for c, m, d in zip(chunks, metadatas, distances)
        ]

        return {"answer": answer, "sources": sources}

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with retrieved context."""
        system_prompt = """You are an intelligent document assistant. 
Answer questions accurately based ONLY on the provided context.
If the answer is not in the context, say "I couldn't find relevant information in the uploaded documents."
Always be concise, helpful, and cite which source you used."""

        user_prompt = f"""Context from documents:
{context}

Question: {question}

Answer based on the context above:"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback: return top chunk if LLM fails
            return f"[LLM Error: {str(e)}]\n\nBest matching content:\n{context[:500]}"

    # ─────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────

    def list_documents(self) -> List[dict]:
        """List all indexed documents."""
        # Refresh from ChromaDB metadata
        if self.collection.count() == 0:
            return []

        results = self.collection.get(include=["metadatas"])
        seen = {}
        for meta in results["metadatas"]:
            src = meta["source"]
            if src not in seen:
                seen[src] = {"name": src, "chunks": 0}
            seen[src]["chunks"] += 1

        return list(seen.values())

    def delete_document(self, doc_name: str) -> bool:
        """Delete all chunks for a document."""
        results = self.collection.get(
            where={"source": doc_name}, include=["metadatas"]
        )
        if not results["ids"]:
            return False

        self.collection.delete(ids=results["ids"])
        self._documents.pop(doc_name, None)
        return True

    def get_vector_count(self) -> int:
        """Total number of vectors stored."""
        return self.collection.count()
