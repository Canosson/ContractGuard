import os
import ssl
import certifi
import pdfplumber
import re

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Configure SSL
ssl_context = ssl.create_default_context(cafile=certifi.where())
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUEST_CA_BUNDLE"] = certifi.where()

# initializing embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    show_progress_bar=False,
    chunk_size=50,
    retry_min_seconds=15
)

# inititalize vector store
vectorstore = PineconeVectorStore(
    index_name=os.environ["INDEX_NAME"], embedding=embeddings
)

def enrich_chunk(clause: dict, contract_title: str) -> dict:
    """Provides a context string (the contract title + a label) to each       
  clause's text and stores the result in clause["embedded_text"]"""
    prefix = f"Contract: {contract_title}\nClause content: "
    clause["embedded_text"] = prefix + clause["text"]
    return clause


def extract_clauses(pdf_path: str, namespace: str) -> list[dict]:
    """Extracts all text page by page (from the PDF) through pdfplumber,
  then splits it into clause segments"""
    clauses = []
    full_text = ""
    contract_title = os.path.basename(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

    # To extract sections and sub-sections
    segments = re.split(r'(?=^\d+(?:\.\d+)*\s+[A-Z])', full_text, flags=re.MULTILINE)

    for segment in segments:
        segment = segment.strip()
        if segment:
            clause = {"text": segment, "source": pdf_path}
            clause = enrich_chunk(clause, contract_title)
            clauses.append(clause)

    vectorstore.add_texts(
        texts=[c["embedded_text"] for c in clauses],
        metadatas=[{"source": c["source"]} for c in clauses],
        namespace=namespace
    )

    return clauses

def retrieve_clauses(query: str, namespace: str, k: int = 5) -> list[str]:
    """Returns the text content of the top k matching clauses from query string"""
    results = vectorstore.similarity_search(query, k=k, namespace=namespace)
    return [doc.page_content for doc in results]
