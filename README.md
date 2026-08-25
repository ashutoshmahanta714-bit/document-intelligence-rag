# DocIntel — Document Intelligence RAG Demo

A full-stack learning demo that accepts documents and answers questions using retrieval-augmented generation (RAG).

> **Learning status:** This repository is being used to study and deploy a RAG application. It is not currently presented as original portfolio work. Understand and rebuild the components before claiming authorship in applications or interviews.

## What it does

1. Extracts text from PDF, DOCX, TXT, CSV, or Markdown files.
2. Splits the text into overlapping chunks.
3. Creates embeddings with OpenAI's `text-embedding-3-small` model.
4. Stores chunks and embeddings in ChromaDB.
5. Retrieves relevant chunks for a question.
6. Generates a grounded answer with `gpt-4o-mini` and displays sources.

## Stack

- FastAPI and Pydantic
- React 18 and Vite
- ChromaDB
- OpenAI API
- PDFPlumber, python-docx, and Pandas
- Docker
- Render Blueprint

## Local setup

### Backend

```bash
git clone https://github.com/ashutoshmahanta714-bit/document-intelligence-rag.git
cd document-intelligence-rag
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Install dependencies and create the local environment file:

```bash
pip install -r requirements.txt

# macOS/Linux
cp .env.example .env

# Windows Command Prompt
copy .env.example .env
```

Edit `.env` and replace only the placeholder value:

```env
OPENAI_API_KEY=your_real_key
APP_USERNAME=docintel
APP_PASSWORD=choose_a_private_demo_password
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
VITE_API_URL=http://localhost:8000
CHROMA_PATH=./chroma_db
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:5173
```

Never commit `.env` or paste your API key into GitHub issues, pull requests, screenshots, or frontend code.

Start the backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

In a second terminal:

```bash
npm install
npm run dev
```

Open http://localhost:5173.

## Deploy on Render

This repository includes:

- `Dockerfile` to build the React frontend and run FastAPI.
- `render.yaml` to create a Render web service.
- A secret placeholder for `OPENAI_API_KEY`; the real key is entered only in Render.

After these files are on `main`:

1. Sign in to [Render](https://dashboard.render.com/).
2. Click **New +** and choose **Blueprint**.
3. Connect GitHub and select `ashutoshmahanta714-bit/document-intelligence-rag`.
4. Render reads `render.yaml`.
5. Enter the two secret values when Render prompts you:
   - `OPENAI_API_KEY`: paste your OpenAI API key.
   - `APP_PASSWORD`: choose a new private password for this demo. Do not reuse your GitHub or email password.
6. Create the Blueprint and wait for the deploy to become **Live**.
7. Open the generated `onrender.com` URL.
8. When the browser asks for credentials, use username `docintel` and the `APP_PASSWORD` you chose.
9. Upload a small text or PDF file and ask a question whose answer appears in that file.

### Free-tier limitation

The Blueprint uses Render's free web-service plan for learning. Free services sleep after inactivity and use an ephemeral filesystem. Uploaded files and the ChromaDB index are therefore lost after a restart, redeploy, or sleep cycle.

For permanent storage, change to a paid Render instance and attach a persistent disk, then set:

```env
CHROMA_PATH=/var/data/chroma_db
UPLOAD_DIR=/var/data/uploads
```

Mount the disk at `/var/data`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/status` | API status |
| `POST` | `/upload` | Parse and index a document |
| `POST` | `/query` | Retrieve context and generate an answer |
| `GET` | `/documents` | List indexed documents |
| `DELETE` | `/documents/{name}` | Remove a document from the vector store |
| `GET` | `/health` | Health and vector-count check |
| `GET` | `/docs` | Interactive FastAPI API documentation |

## Important limitations

- No authentication or per-user document isolation.
- The demo uses HTTP Basic authentication; keep `APP_PASSWORD` private.
- OpenAI API usage is billed to the account that owns `OPENAI_API_KEY`.
- The free Render filesystem is temporary.
- Scanned PDFs need OCR before indexing.
- This is a learning demo, not a production service.
