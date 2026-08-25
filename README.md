# DocIntel — Document Intelligence RAG System

A full-stack Retrieval-Augmented Generation application that lets users upload documents and ask grounded questions about their contents.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-orange)](https://www.trychroma.com/)

## Recruiter Snapshot

| Area | Implementation |
|---|---|
| Problem | Find answers inside user-provided documents without manually searching every file |
| Data pipeline | Parse → clean → chunk with overlap → embed → persist |
| Retrieval | Sentence-transformer embeddings with ChromaDB cosine similarity |
| Generation | LLM answer constrained by retrieved context |
| Backend | FastAPI endpoints for upload, query, listing, deletion, and health checks |
| Frontend | React/Vite interface for document upload, chat, sources, and document management |
| Supported files | PDF, DOCX, TXT, CSV, and Markdown |

## System Flow

```text
Document upload
      ↓
Text extraction and cleaning
      ↓
Overlapping text chunks
      ↓
Sentence-transformer embeddings
      ↓
ChromaDB vector store
      ↓
User question → similarity search → retrieved context → LLM answer + sources
```

## Features

- Upload and index PDF, DOCX, TXT, CSV, and Markdown files.
- Split text into overlapping chunks for better retrieval coverage.
- Generate local embeddings with `all-MiniLM-L6-v2`.
- Persist embeddings and metadata in ChromaDB.
- Retrieve the most relevant chunks using cosine similarity.
- Generate grounded answers from retrieved context.
- Display source names, chunk numbers, relevance scores, and excerpts.
- List indexed documents and remove them from the vector store.
- Inspect API health and current vector count.

## Technology Stack

### Data and AI

- Python
- Pandas
- Sentence Transformers
- ChromaDB
- OpenAI-compatible LLM API
- PDFPlumber and python-docx

### Application

- FastAPI and Pydantic
- React 18
- Vite
- REST APIs

## Repository Structure

```text
.
├── main.py             # FastAPI application and endpoints
├── rag_engine.py       # Parsing, chunking, embeddings, retrieval, and generation
├── requirements.txt    # Python dependencies
├── App.jsx             # Frontend state and API integration
├── App.css             # Application styling
├── Upload.jsx          # File upload component
├── Chat.jsx            # Chat and source display
├── Documents.jsx       # Indexed-document management
├── main.jsx            # React entry point
├── index.html          # Vite HTML entry
├── package.json        # Frontend dependencies and scripts
├── vite.config.js      # Vite development configuration
└── .env.example        # Safe environment-variable template
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/ashutoshmahanta714-bit/document-intelligence-rag.git
cd document-intelligence-rag
```

### 2. Configure the Python backend

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
# macOS/Linux
cp .env.example .env

# Windows Command Prompt
copy .env.example .env
```

Then replace the placeholder key in `.env`:

```env
OPENAI_API_KEY=your_api_key
LLM_MODEL=gpt-3.5-turbo
VITE_API_URL=http://localhost:8000
```

Never commit the real `.env` file.

### 3. Start the backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs

### 4. Start the frontend

Open a second terminal:

```bash
npm install
npm run dev
```

Open http://localhost:5173.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | API status message |
| `POST` | `/upload` | Parse and index a document |
| `POST` | `/query` | Retrieve context and generate an answer |
| `GET` | `/documents` | List indexed documents |
| `DELETE` | `/documents/{name}` | Remove a document from the vector store |
| `GET` | `/health` | Report health, document count, and vector count |

Example query:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What are the main findings?\",\"top_k\":5}"
```

## Core RAG Decisions

- **Local embeddings:** Sentence Transformers reduces external API calls during indexing.
- **Persistent vector storage:** ChromaDB keeps indexed content between application restarts.
- **Chunk overlap:** Overlapping chunks reduce information loss at chunk boundaries.
- **Grounded prompt:** The model is instructed to answer only from retrieved context.
- **Retrieval transparency:** Source metadata and excerpts are returned with each answer.

## Current Limitations

- The application is intended for local development and demonstration.
- Authentication and per-user document isolation are not implemented.
- Uploaded files are stored locally.
- Automated tests, evaluation datasets, and production deployment are future improvements.
- Scanned PDFs require an OCR pipeline before their text can be indexed.

## Roadmap

- Add automated unit and API tests.
- Add retrieval evaluation metrics such as Precision@K and answer faithfulness.
- Add OCR support for scanned documents.
- Add authentication and separate vector collections per user.
- Containerise the backend and frontend.
- Deploy a public demo with secure secret management.

## Author

**Ashutosh Mahanta** — Data Science and Machine Learning aspirant with experience in Python, SQL, Scikit-learn, OpenCV, predictive maintenance, and applied AI.

- GitHub: [ashutoshmahanta714-bit](https://github.com/ashutoshmahanta714-bit)
- Related work: Industrial Motor Fault Detection using Machine Learning and SWIR sensor image processing with OpenCV.
