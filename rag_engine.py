"""Core retrieval-augmented generation logic."""

import os
import re
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class RAGEngine:
    def __init__(
        self,
        collection_name: str = "documents",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=api_key) if api_key else None

        base_dir = Path(__file__).resolve().parent
        chroma_path = Path(os.getenv("CHROMA_PATH", "chroma_db")).expanduser()
        if not chroma_path.is_absolute():
            chroma_path = base_dir / chroma_path
        chroma_path.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _require_openai(self) -> OpenAI:
        if self.openai_client is None:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured on the server."
            )
        return self.openai_client

    def _embed(self, texts: List[str]) -> List[List[float]]:
        client = self._require_openai()
        response = client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def ingest_document(self, file_path: str, original_name: str) -> int:
        """Parse, chunk, embed, and store a document."""
        ext = Path(file_path).suffix.lower()
        text = self._parse_document(file_path, ext)
        if not text.strip():
            raise ValueError("Document appears to be empty or unreadable.")

        chunks = self._split_text(text)
        embeddings = self._embed(chunks)

        ids = [f"{original_name}_{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "source": original_name,
                "chunk_index": index,
                "file_path": file_path,
            }
            for index in range(len(chunks))
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def _parse_document(self, file_path: str, ext: str) -> str:
        """Extract text from supported document types."""
        if ext in {".txt", ".md"}:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                return handle.read()

        if ext == ".pdf":
            import pdfplumber

            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            return text

        if ext == ".docx":
            from docx import Document

            document = Document(file_path)
            return "\n".join(paragraph.text for paragraph in document.paragraphs)

        if ext == ".csv":
            import pandas as pd

            dataframe = pd.read_csv(file_path)
            return dataframe.to_string(index=False)

        raise ValueError(f"Unsupported file type: {ext}")

    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping word chunks."""
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

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant chunks and generate a grounded answer."""
        if self.collection.count() == 0:
            return {
                "answer": (
                    "No documents have been indexed yet. "
                    "Please upload a document first."
                ),
                "sources": [],
            }

        query_embedding = self._embed([question])
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        context = "\n\n".join(
            f"[Source: {metadata['source']}, Chunk {metadata['chunk_index']}]\n{chunk}"
            for chunk, metadata in zip(chunks, metadatas)
        )
        answer = self._generate_answer(question, context)

        sources = [
            {
                "source": metadata["source"],
                "chunk_index": metadata["chunk_index"],
                "relevance_score": round(1 - distance, 4),
                "excerpt": chunk[:200] + "..." if len(chunk) > 200 else chunk,
            }
            for chunk, metadata, distance in zip(
                chunks, metadatas, distances
            )
        ]
        return {"answer": answer, "sources": sources}

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using only retrieved context."""
        client = self._require_openai()
        response = client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a document assistant. Answer accurately using "
                        "only the provided context. If the answer is absent, say "
                        "you could not find it in the uploaded documents. Be "
                        "concise and name the source used."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Context from documents:\n{context}\n\n"
                        f"Question: {question}\n\n"
                        "Answer based on the context above:"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        return response.choices[0].message.content or "No answer was generated."

    def list_documents(self) -> List[dict]:
        """List indexed documents from ChromaDB metadata."""
        if self.collection.count() == 0:
            return []

        results = self.collection.get(include=["metadatas"])
        seen: Dict[str, dict] = {}
        for metadata in results["metadatas"]:
            source = metadata["source"]
            if source not in seen:
                seen[source] = {"name": source, "chunks": 0}
            seen[source]["chunks"] += 1
        return list(seen.values())

    def delete_document(self, doc_name: str) -> bool:
        """Delete all chunks for one document."""
        results = self.collection.get(
            where={"source": doc_name},
            include=["metadatas"],
        )
        if not results["ids"]:
            return False

        self.collection.delete(ids=results["ids"])
        return True

    def get_vector_count(self) -> int:
        """Return the total number of stored vectors."""
        return self.collection.count()
