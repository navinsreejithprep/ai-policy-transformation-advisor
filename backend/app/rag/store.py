import chromadb
from pathlib import Path
from ..config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.resolved_chroma_path())
    return _client

def get_collection():
    return get_client().get_or_create_collection(
        name="policy_knowledge",
        metadata={"hnsw:space": "cosine"}
    )
