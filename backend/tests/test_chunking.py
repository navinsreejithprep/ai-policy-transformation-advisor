from app.rag.ingest import chunk_text

def test_chunking():
    text = "a " * 2000
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)
