import os
from dotenv import load_dotenv, find_dotenv
from ingestion import retrieve_clauses
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from prompt import SYSTEM_PROMPT

load_dotenv(find_dotenv())

# Openai as LLM
model = init_chat_model(model="gpt-5.2", model_provider="openai")

# Initializing embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Inititalize vector store
vectorstore = PineconeVectorStore(
    index_name=os.environ["INDEX_NAME"], embedding=embeddings
)

def run_full_scan(clauses: list[dict]) -> str:
    """Full scan of the uploaded PDF file and run against the System Prompt"""
    contract_text = "\n\n".join(c["embedded_text"] for c in clauses)
    response = model.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", f"Please review the following contract cluses:\n{contract_text}"),
    ])
    return response.content or "" # type: ignore[arg-type]

def answer_question(question: str, namespace: str) -> str:
    """Answering user questions based on the generated report"""
    chunks = retrieve_clauses(question, namespace=namespace, k=5)
    context = "\n\n".join(chunks)
    response = model.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", f"Answer the following question based only on the contract clauses provided.\n\nQuestion:{question}\n\nContract clauses:\n{context}")
    ])
    return response.content or "" # type: ignore[arg-type]




