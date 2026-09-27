import pytest

from app.config import settings


@pytest.fixture
def isolated_kb(tmp_path, monkeypatch):
    """Points the vector store and knowledge base at a throwaway tmp_path dir and
    resets the module-level Chroma client singleton, so tests never touch the
    real dev database and don't leak state into each other."""
    import app.rag.store as store_module

    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    chroma_dir = tmp_path / "chroma_db"

    monkeypatch.setattr(settings, "knowledge_base_path", str(kb_dir))
    monkeypatch.setattr(settings, "vector_db_path", str(chroma_dir))

    store_module._client = None
    yield kb_dir
    store_module._client = None
