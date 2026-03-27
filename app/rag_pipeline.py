import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from app.retriever import get_faiss_index

load_dotenv()

# Using Groq LLM. Required: GROQ_API_KEY in .env file or environment
def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
    )

def ask_rag(query: str) -> str:
    """Answers a question based on uploaded policies."""
    vectorstore = get_faiss_index()
    if not vectorstore:
        return "No documents uploaded or indexed yet."
        
    llm = get_llm()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    system_prompt = (
        "You are an expert insurance and policy analysis assistant. "
        "Use the following pieces of retrieved context to answer the user's question accurately. "
        "If you don't know the answer based on the context, say that you don't know. "
        "Highlight exactly where in the policy (e.g., document name) the answer was found if possible. "
        "Keep your answers concise and informative.\n\n"
        "Context:\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    response = rag_chain.invoke({"input": query})
    return response["answer"]

def summarize_policies() -> str:
    """Generates a high-level summary of the indexed policy corpus."""
    vectorstore = get_faiss_index()
    if not vectorstore:
        return "No documents to summarize."
    
    llm = get_llm()
    # Simple semantic search to find top chunks related to summary or overview
    docs = vectorstore.similarity_search("insurance policy summary overview coverage", k=5)
    
    context = "\n".join([f"Source: {d.metadata.get('source', 'Unknown')}\n{d.page_content}" for d in docs])
    
    prompt = (
        "Based on the following excerpts from insurance policies, provide a cohesive "
        "high-level summary of the policies, focusing on the main covered items, generic terms, "
        "and overall purpose.\n\n"
        f"Excerpts:\n{context}"
    )
    
    response = llm.invoke(prompt)
    return response.content

def extract_key_clauses() -> dict:
    """Extracts Coverage, Exclusions, and Premium details using targeted QA."""
    coverage = ask_rag("What specific items, scenarios, or risks are covered under this policy? Provide a detailed list.")
    exclusions = ask_rag("What are the strict exclusions, limitations, or things explicitly NOT covered under this policy?")
    premium = ask_rag("What is the premium amount, deductible structure, or payment schedule described in this policy?")
    
    return {
        "Coverage": coverage,
        "Exclusions": exclusions,
        "Premium": premium
    }
