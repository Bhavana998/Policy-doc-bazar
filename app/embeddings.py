import os
from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model():
    """Initializes and returns the HuggingFace embedding model."""
    # Using all-MiniLM-L6-v2 as it's efficient for semantic search
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
