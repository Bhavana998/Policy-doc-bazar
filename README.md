# PolicyBazaar-Style Document Analysis (RAG)

An end-to-end Python REST API using FastAPI, LangChain, FAISS, and OpenAI to ingest insurance documents (PDFs), parse them intelligently (with fallback OCR via Tesseract), index them into a local vector store, and answer user queries against the knowledge base.

## Prerequisites

1. Python 3.9+
2. Tesseract OCR (Optional, required for scanned image text extraction).
   * **Windows**: Download [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and install. Add it to your System PATH (`C:\Program Files\Tesseract-OCR`).
3. An OpenAI API Key.

## Setup Instructions

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up Environment Variables:**
Create a `.env` file in the root directory and add your OpenAI Key:
```
OPENAI_API_KEY="sk-..."
```

3. **Start the FastAPI server:**
```bash
uvicorn app.main:app --reload
```

The application will launch on `http://localhost:8000`. You can visit Swagger UI at `http://localhost:8000/docs` to test the API visually.

## API Endpoints

### 1. Upload a Document
Uploads and indexes a PDF.
**Endpoint:** `POST /upload-document`
```bash
curl -X 'POST' \
  'http://localhost:8000/upload-document' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample_policy.pdf'
```

### 2. Ask a Question
Asks a natural language question about the uploaded policies.
**Endpoint:** `POST /ask-question`
```bash
curl -X 'POST' \
  'http://localhost:8000/ask-question' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is covered in this insurance policy?"}'
```

### 3. Summarize Policies
Generates a brief summary of all indexed policies.
**Endpoint:** `GET /summarize`
```bash
curl -X 'GET' 'http://localhost:8000/summarize' -H 'accept: application/json'
```

### 4. Extract Key Clauses
Automatically builds specialized QA queries to fetch key clauses like Coverage, Exclusions, and Premium.
**Endpoint:** `GET /extract-clauses`
```bash
curl -X 'GET' 'http://localhost:8000/extract-clauses' -H 'accept: application/json'
```
