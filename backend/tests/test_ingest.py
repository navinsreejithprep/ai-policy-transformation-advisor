from pathlib import Path

from app.rag.ingest import (
    IngestionError,
    _split_text_into_pages,
    chunk_text,
    clean_text,
    ingest_document,
    ingest_text,
)


def test_chunking():
    text = "a " * 2000
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_clean_text_strips_control_chars_and_extra_whitespace():
    dirty = "Hello\x00World\t\t  multiple   spaces\r\n"
    cleaned = clean_text(dirty)
    assert "\x00" not in cleaned
    assert "  " not in cleaned.replace("\n", "")


def test_split_text_into_pages_without_markers_is_single_page():
    pages = _split_text_into_pages("just some plain text")
    assert pages == [(1, "just some plain text")]


def test_split_text_into_pages_with_markers():
    raw = "preamble\n[PAGE 41]\nfirst page body\n[PAGE 43]\nsecond page body\n"
    pages = _split_text_into_pages(raw)
    page_numbers = [p[0] for p in pages]
    assert 41 in page_numbers and 43 in page_numbers
    assert "first page body" in dict(pages)[41]
    assert "second page body" in dict(pages)[43]


def test_ingest_text_rejects_empty_file(tmp_path, isolated_kb):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n  ")
    try:
        ingest_text(empty_file)
        assert False, "expected IngestionError"
    except IngestionError:
        pass


def test_ingest_document_rejects_unsupported_extension(tmp_path, isolated_kb):
    bad_file = tmp_path / "notes.docx"
    bad_file.write_text("hello")
    try:
        ingest_document(bad_file)
        assert False, "expected IngestionError"
    except IngestionError:
        pass


def test_ingest_detects_section_heading_from_page_not_mangled_chunk(tmp_path, isolated_kb):
    """Regression test: chunk_text() joins all whitespace onto one line, so section
    detection must run on the pre-chunk page text (which still has real line breaks),
    not on the already-chunked text — otherwise the heuristic can never match."""
    from app.rag.store import get_collection

    doc = tmp_path / "with_heading.txt"
    doc.write_text("Programme Overview\n" + ("This is body text about the programme. " * 40))

    ingest_text(doc, is_demo=True)

    collection = get_collection()
    data = collection.get(include=["metadatas"])
    sections = {m["section"] for m in data["metadatas"]}
    assert "Programme Overview" in sections


def test_ingest_text_adds_chunks_to_collection(tmp_path, isolated_kb):
    from app.rag.store import get_collection

    doc = tmp_path / "sample.txt"
    doc.write_text("This is a small demo document about a fictional pilot programme. " * 5)

    added = ingest_text(doc, is_demo=True)
    assert added > 0

    collection = get_collection()
    assert collection.count() == added

    data = collection.get(include=["metadatas"])
    assert all(m["document_name"] == "sample.txt" for m in data["metadatas"])
    assert all(m["is_demo_data"] is True for m in data["metadatas"])
