# ◈ DocIntel — Document Intelligence RAG System

A full-stack RAG (Retrieval-Augmented Generation) system to chat with your documents.

```
PDF / DOCX / TXT / CSV
        ↓
    Chunking + Embeddings
        ↓
    ChromaDB Vector Store
        ↓
User Query → Similarity Search → LLM → Grounded Answer ✅
```

---

## 🗂 Project Structure

```
rag-project/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── rag_engine.py     # Core RAG logic
│   ├── requirements.txt  # Python dependencies
│   └── .env              # API keys & config
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── components/
    │       ├── Upload.jsx
    │       ├── Chat.jsx
    │       └── Documents.jsx
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## ⚡ Quick Setup

### Step 1 — Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI key to .env
OPENAI_API_KEY=sk-your-key-here
```

### Step 2 — Start Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs → http://localhost:8000/docs

### Step 3 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Open → http://localhost:5173

---

## 🌐 Expose with Ngrok

```bash
# Install ngrok
npm install -g ngrok

# In a new terminal, expose backend
ngrok http 8000
# → https://abc123.ngrok.io

# Update frontend to use ngrok URL
# Set VITE_API_URL=https://abc123.ngrok.io in frontend/.env

# Expose frontend too (optional)
ngrok http 5173
# → https://xyz456.ngrok.io (share this URL)
```

---

## 🔧 Using Free/Local LLM (No OpenAI cost)

Install [Ollama](https://ollama.com) and update `.env`:

```env
OPENAI_API_KEY=ollama
LLM_MODEL=llama3
OPENAI_BASE_URL=http://localhost:11434/v1
```

Run: `ollama pull llama3`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload & index a document |
| POST | `/query` | Ask a question |
| GET | `/documents` | List indexed documents |
| DELETE | `/documents/{name}` | Remove a document |
| GET | `/health` | System health check |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB (local persistent) |
| LLM | OpenAI GPT / Ollama (local) |
| Frontend | React + Vite |
| Tunnel | Ngrok |
