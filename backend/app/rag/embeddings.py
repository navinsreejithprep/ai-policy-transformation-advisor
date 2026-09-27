"""Embedding generation, with a provider switch.

Default is OpenAI's hosted embeddings API ("openai") — this is what makes the
backend deployable on constrained hosts: importing sentence-transformers pulls
in torch + transformers (100+ transitive packages), which is heavy enough to
blow past free-tier CPU/build limits on hosts like Render. Since this app
already requires an OpenAI API key for every LLM call, using OpenAI for
embeddings too adds no new external dependency, just a per-call cost of
fractions of a cent (text-embedding-3-small).

A "local" provider (real sentence-transformers) is kept for the test suite, so
tests exercise genuine semantic similarity without needing network calls, an
API key, or incurring cost on every test run — see tests/conftest.py. The
sentence-transformers import is deliberately lazy (inside _get_local_model)
so a production install that only has requirements.txt (no
sentence-transformers) never touches that code path and never fails to import.
"""
from openai import OpenAI

from ..config import settings

_openai_client: OpenAI | None = None
_local_model = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(settings.embedding_model)
    return _local_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.embedding_provider == "local":
        return _get_local_model().encode(texts).tolist()
    response = _get_openai_client().embeddings.create(
        model=settings.openai_embedding_model, input=texts
    )
    return [item.embedding for item in response.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
