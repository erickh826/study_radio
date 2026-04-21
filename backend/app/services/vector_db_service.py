"""
Vector DB service for document storage and RAG retrieval (Agent B foundation).
Uses ChromaDB with local persistence.
"""
import re
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils import embedding_functions


_CHROMA_PATH = "./chroma_db"
_CHUNK_SIZE = 500       # characters per chunk
_CHUNK_OVERLAP = 50     # overlap between consecutive chunks


def _get_collection(job_id: str):
    client = chromadb.PersistentClient(path=_CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=f"job_{job_id}",
        embedding_function=ef,
    )


def _chunk_text(text: str) -> List[str]:
    """Split text into overlapping chunks on sentence boundaries where possible."""
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) <= _CHUNK_SIZE:
            current += sentence
        else:
            if current:
                chunks.append(current.strip())
            # Start new chunk with overlap from end of previous chunk
            current = current[-_CHUNK_OVERLAP:] + sentence if current else sentence
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c]


def store_document(job_id: str, text: str) -> int:
    """
    Chunk and embed document text, persisted under the given job_id namespace.
    Returns the number of chunks stored.
    """
    chunks = _chunk_text(text)
    if not chunks:
        return 0

    collection = _get_collection(job_id)
    collection.add(
        documents=chunks,
        ids=[f"{job_id}_chunk_{i}" for i in range(len(chunks))],
    )
    return len(chunks)


def retrieve_context(job_id: str, query: str, top_k: int = 3) -> str:
    """
    Retrieve the most relevant chunks for a query from the job's document store.
    Returns chunks joined as a single string, ready to pass to Agent B.
    """
    collection = _get_collection(job_id)
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
    )
    docs = results.get("documents", [[]])[0]
    return "\n\n".join(docs)
