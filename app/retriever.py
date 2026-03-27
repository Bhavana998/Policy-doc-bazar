import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.embeddings import get_embedding_model

VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "vector_store")

def get_faiss_index():
    """Loads an existing FAISS index or returns None if it doesn't exist."""
    embeddings = get_embedding_model()
    if os.path.exists(os.path.join(VECTOR_STORE_PATH, "index.faiss")):
        # We allow dangerous deserialization here as we are loading local files we created
        return FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    return None

def store_documents(chunks):
    """Stores a list of chunk dictionaries into the FAISS index."""
    embeddings = get_embedding_model()
    documents = [Document(page_content=chunk["page_content"], metadata=chunk["metadata"]) for chunk in chunks]
    
    vectorstore = get_faiss_index()
    if vectorstore:
        vectorstore.add_documents(documents)
    else:
        vectorstore = FAISS.from_documents(documents, embeddings)
        
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vectorstore.save_local(VECTOR_STORE_PATH)

def retrieve_context(query: str, k: int = 4):
    """Retrieves top-k relevant chunks from FAISS for a given query."""
    vectorstore = get_faiss_index()
    if not vectorstore:
        return []
        
    docs = vectorstore.similarity_search(query, k=k)
    return docs
