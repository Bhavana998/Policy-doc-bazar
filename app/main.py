import os
import shutil
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Fix for Python 3.8 compatibility with newer libraries
if sys.version_info < (3, 10):
    try:
        from importlib_metadata import packages_distributions
        import importlib.metadata
        importlib.metadata.packages_distributions = packages_distributions
    except ImportError:
        pass

# Load environment variables at the very beginning
load_dotenv()

from app.utils import extract_text_from_pdf, chunk_text
from app.retriever import store_documents
from app.rag_pipeline import ask_rag, summarize_policies, extract_key_clauses

app = FastAPI(
    title="PolicyBazaar Document Analysis API",
    description="RAG-based API to analyze and query insurance policies and legal documents.",
    version="1.0"
)

os.makedirs("data", exist_ok=True)
os.makedirs("vector_store", exist_ok=True)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str

class ClauseResponse(BaseModel):
    Coverage: str
    Exclusions: str
    Premium: str

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF policy document to be indexed in the vector database."""
    if not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
        
    file_path = os.path.join("data", file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
            if not text.strip():
                raise HTTPException(status_code=422, detail="Could not extract text. Check if PDF is readable.")
                
            chunks = chunk_text(text, metadata={"source": file.filename})
            store_documents(chunks)
        else:
            raise HTTPException(status_code=501, detail="DOCX support coming soon. Please use PDF.")
            
        return {"message": f"Successfully processed and indexed {file.filename}", "chunks_stored": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-question", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a question based on indexed policy documents."""
    try:
        answer = ask_rag(request.query)
        return QueryResponse(query=request.query, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

@app.get("/summarize")
async def summarize():
    """Generates a high-level summary of the indexed policies."""
    try:
        summary = summarize_policies()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

@app.get("/extract-clauses", response_model=ClauseResponse)
async def extract_clauses():
    """Extracts standard Coverage, Exclusions, and Premium clauses."""
    try:
        clauses = extract_key_clauses()
        return clauses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
