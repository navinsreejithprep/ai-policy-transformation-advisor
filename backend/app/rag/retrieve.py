import re

from sentence_transformers import SentenceTransformer

from ..config import settings
from ..models.schemas import SourceCitation
from .store import get_collection

_CHUNK_INDEX_RE = re.compile(r"-c(\d+)-")

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def retrieve_evidence(
    query: str,
    top_k: int = None,
    filters: dict | None = None,
    relevance_threshold: float | None = None,
) -> list[dict]:
    """Semantic retrieval with metadata filtering, source dedup and a relevance
    floor. Returns dicts with text/document/page/similarity/metadata — the
    similarity score is kept for internal ranking/thresholding but is not surfaced
    to end users in API responses (spec §7)."""
    top_k = top_k or settings.top_k_default
    threshold = settings.retrieval_relevance_threshold if relevance_threshold is None else relevance_threshold

    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = _get_model().encode([query]).tolist()
    # over-fetch so dedup/threshold still leaves ~top_k useful results
    n_results = min(max(top_k * 3, top_k), collection.count())

    result = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=filters or None,
        include=["documents", "metadatas", "distances"],
    )

    rows = []
    seen_documents: dict[str, float] = {}
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    for text, metadata, distance in zip(docs, metas, dists):
        similarity = 1 - distance  # cosine space: distance = 1 - cosine_similarity
        if similarity < threshold:
            continue

        dedup_key = f"{metadata.get('document_name')}|{metadata.get('page_number')}"
        if dedup_key in seen_documents and seen_documents[dedup_key] >= similarity:
            continue
        seen_documents[dedup_key] = similarity

        rows.append(
            {
                "text": text,
                "document": metadata.get("document_name"),
                "page": metadata.get("page_number"),
                "similarity": round(similarity, 4),
                "metadata": metadata,
            }
        )

    rows.sort(key=lambda r: r["similarity"], reverse=True)
    return rows[:top_k]


# Backwards-compatible alias used by earlier code / tests.
def retrieve(query: str, top_k: int = 5) -> list[dict]:
    rows = retrieve_evidence(query, top_k=top_k)
    return [
        {"text": r["text"], "metadata": r["metadata"], "distance": 1 - r["similarity"]}
        for r in rows
    ]


def get_document_text(document_name: str) -> str:
    """Reconstruct a stored document's text from its chunks, in original page/chunk
    order, so it can be reused as analysis input (e.g. "analyze this uploaded PDF").
    Adjacent chunks overlap slightly (CHUNK_OVERLAP) so the rebuilt text has minor
    duplicated text at chunk boundaries — a documented, acceptable imperfection for
    a POC rather than storing the original full text separately."""
    collection = get_collection()
    data = collection.get(where={"document_name": document_name}, include=["documents", "metadatas"])
    ids = data.get("ids", [])
    if not ids:
        return ""

    def sort_key(i: int):
        page = data["metadatas"][i].get("page_number") or 0
        match = _CHUNK_INDEX_RE.search(ids[i])
        chunk_index = int(match.group(1)) if match else 0
        return (page, chunk_index)

    order = sorted(range(len(ids)), key=sort_key)
    return "\n\n".join(data["documents"][i] for i in order)


def rows_to_citations(rows: list[dict]) -> list[SourceCitation]:
    citations = []
    for r in rows:
        m = r["metadata"]
        citations.append(
            SourceCitation(
                document_name=m.get("document_name", "unknown"),
                page_number=m.get("page_number"),
                section=m.get("section") or None,
                chunk_id=m.get("chunk_id"),
                is_demo_data=bool(m.get("is_demo_data", False)),
                passage_preview=r["text"],
            )
        )
    return citations
