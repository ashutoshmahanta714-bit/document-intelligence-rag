FROM node:22-alpine AS frontend

WORKDIR /build
COPY package*.json ./
RUN npm install
COPY index.html vite.config.js main.jsx App.jsx App.css Chat.jsx Upload.jsx Documents.jsx ./
RUN npm run build


FROM python:3.11-slim AS application

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py rag_engine.py ./
COPY --from=frontend /build/dist ./dist

RUN mkdir -p /tmp/uploads /tmp/chroma_db

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
