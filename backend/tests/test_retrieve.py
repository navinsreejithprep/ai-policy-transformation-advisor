from pathlib import Path

from app.rag.ingest import chunk_text, ingest_text
from app.rag.retrieve import get_document_text, retrieve_evidence


def test_retrieve_returns_empty_on_empty_collection(isolated_kb):
    rows = retrieve_evidence("anything", top_k=5)
    assert rows == []


def test_retrieve_finds_relevant_chunk_and_dedupes(tmp_path, isolated_kb):
    doc = tmp_path / "risk.txt"
    doc.write_text(
        "The vendor missed two milestone deadlines due to underestimated integration effort "
        "with the legacy case management system. This caused a significant delivery delay. " * 3
    )
    ingest_text(doc, is_demo=True)

    rows = retrieve_evidence("vendor delivery delay integration risk", top_k=5)
    assert len(rows) > 0
    assert rows[0]["document"] == "risk.txt"
    # dedup: no two rows should share the same (document, page) key
    keys = [(r["document"], r["page"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_retrieve_applies_relevance_threshold(tmp_path, isolated_kb):
    doc = tmp_path / "unrelated.txt"
    doc.write_text("Recipe for baking sourdough bread with a long fermentation time.")
    ingest_text(doc, is_demo=True)

    rows = retrieve_evidence("quantum computing supply chain logistics risk", top_k=5, relevance_threshold=0.6)
    assert rows == [] or all(r["similarity"] >= 0.6 for r in rows)


def test_get_document_text_returns_empty_for_unknown_document(isolated_kb):
    assert get_document_text("does_not_exist.pdf") == ""


def test_get_document_text_reassembles_chunks_in_order(tmp_path, isolated_kb):
    # Force multiple chunks so reassembly order is actually exercised.
    doc = tmp_path / "multi_chunk.txt"
    doc.write_text(
        "Section one content. " * 30 + "Section two content follows here. " * 30 + "Section three wraps up. " * 30
    )
    ingest_text(doc, is_demo=False)

    chunks = chunk_text(doc.read_text())
    assert len(chunks) > 1, "test setup should produce multiple chunks"

    rebuilt = get_document_text("multi_chunk.txt")
    assert "Section one content." in rebuilt
    assert "Section three wraps up." in rebuilt
    # order preserved: "one" text appears before "three" text
    assert rebuilt.index("Section one") < rebuilt.index("Section three")
