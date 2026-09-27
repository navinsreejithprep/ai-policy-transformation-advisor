import re
import uuid
from pathlib import Path

import fitz
from sentence_transformers import SentenceTransformer

from ..config import settings
from ..utils.logging import get_logger
from .store import get_collection

logger = get_logger(__name__)

_model = None

DEMO_DIR_NAME = "demo"
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

# Categorizes the bundled demo corpus so the Knowledge Base UI can show what each
# tab's documents are actually for, out of the box. Purely a display label — an
# uploaded document with no matching entry here just falls back to "other".
DEMO_CATEGORY_MAP = {
    "demo_policy.txt": "policy",
    "evidence_digital_literacy_survey.txt": "evidence",
    "annual_report_2025_excerpt.txt": "evidence",
    "evaluation_pilot_program_outcomes.txt": "evidence",
    "benchmark_international_case_estlandia.txt": "benchmark",
    "risk_case_study_prior_rollout.txt": "risk",
    "stakeholder_consultation_summary.txt": "stakeholder",
    "budget_and_funding_note.txt": "budget",
}


class IngestionError(Exception):
    """Raised when a document cannot be parsed or contains no extractable text."""


def embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters picked up from PDF extraction."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap if overlap is not None else settings.chunk_overlap
    text = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _detect_section_heading(text_with_newlines: str) -> str | None:
    """Best-effort heuristic: if the text opens with a short, title-like line, treat
    it as a section heading. This is a design choice, not a real document-structure
    parser — flagged explicitly in docs/rag-design.md.

    Must be called on text that still has its original line breaks (i.e. before
    chunk_text(), which joins everything onto one line) or the first line will
    just be the whole chunk and this will never match."""
    first_line = text_with_newlines.split("\n", 1)[0].strip()
    if 3 <= len(first_line) <= 80 and not first_line.endswith("."):
        return first_line
    return None


def _upsert_chunks(
    collection,
    document_name: str,
    document_type: str,
    is_demo: bool,
    page_no: int,
    text: str,
    source: str,
    category: str = "other",
):
    cleaned = clean_text(text)
    if not cleaned.strip():
        return 0
    # Detected once per page/text-block, before chunk_text() destroys line breaks.
    section = _detect_section_heading(cleaned) or ""
    chunks = chunk_text(cleaned)
    if not chunks:
        return 0
    embeddings = embedding_model().encode(chunks).tolist()
    ids = [f"{document_name}-p{page_no}-c{i}-{uuid.uuid4().hex[:6]}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_name": document_name,
            "document_type": document_type,
            "page_number": page_no,
            "section": section,
            "source": source,
            "publication_date": "",
            "chunk_id": ids[i],
            "is_demo_data": is_demo,
            "category": category,
        }
        for i in range(len(chunks))
    ]
    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    return len(chunks)


def ingest_pdf(path: Path, is_demo: bool = False, category: str = "other") -> int:
    try:
        doc = fitz.open(path)
    except Exception as exc:  # malformed / corrupt / password-protected PDF
        raise IngestionError(f"Could not open PDF '{path.name}': {exc}") from exc

    if doc.page_count == 0:
        raise IngestionError(f"'{path.name}' has no pages.")

    collection = get_collection()
    added = 0
    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text")
        added += _upsert_chunks(
            collection,
            document_name=path.name,
            document_type="pdf",
            is_demo=is_demo,
            page_no=page_no,
            text=text,
            source=str(path),
            category=category,
        )
    if added == 0:
        raise IngestionError(
            f"'{path.name}' contains no extractable text (it may be a scanned image PDF)."
        )
    logger.info("ingested document=%s chunks=%d demo=%s", path.name, added, is_demo)
    return added


_PAGE_MARKER = re.compile(r"^\[PAGE (\d+)\]\s*$", re.MULTILINE)


def _split_text_into_pages(raw: str) -> list[tuple[int, str]]:
    """Plain text/markdown demo docs can opt into page-like citations by inserting
    a `[PAGE n]` marker line, e.g. to reproduce a realistic '[Source: X, p. 43]'
    citation. Docs with no markers are treated as a single page."""
    matches = list(_PAGE_MARKER.finditer(raw))
    if not matches:
        return [(1, raw)]

    pages = []
    preamble = raw[: matches[0].start()].strip()
    if preamble:
        pages.append((1, preamble))
    for i, match in enumerate(matches):
        page_no = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        pages.append((page_no, raw[start:end]))
    return pages


def ingest_text(path: Path, is_demo: bool = False, category: str = "other") -> int:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if not raw.strip():
        raise IngestionError(f"'{path.name}' is empty.")
    collection = get_collection()
    added = 0
    for page_no, page_text in _split_text_into_pages(raw):
        added += _upsert_chunks(
            collection,
            document_name=path.name,
            document_type="text",
            is_demo=is_demo,
            page_no=page_no,
            text=page_text,
            source=str(path),
            category=category,
        )
    if added == 0:
        raise IngestionError(f"'{path.name}' produced no chunks after cleaning.")
    logger.info("ingested document=%s chunks=%d demo=%s", path.name, added, is_demo)
    return added


def ingest_document(path: Path, is_demo: bool = False, category: str = "other") -> int:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return ingest_pdf(path, is_demo=is_demo, category=category)
    if suffix in {".txt", ".md"}:
        return ingest_text(path, is_demo=is_demo, category=category)
    raise IngestionError(f"Unsupported file type '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}")


def delete_document(document_name: str) -> int:
    collection = get_collection()
    existing = collection.get(where={"document_name": document_name}, include=[])
    ids = existing.get("ids", [])
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def reindex_all(knowledge_base_path: Path) -> dict:
    """Wipe and rebuild the vector store from every file currently on disk under
    knowledge_base/. Used by POST /documents/index and on startup to auto-seed the
    demo knowledge base so the app is usable without any manual setup."""
    from .store import get_client

    client = get_client()
    try:
        client.delete_collection("policy_knowledge")
    except Exception:
        pass

    collection = get_collection()
    results = {"documents": 0, "chunks": 0, "errors": []}
    if not knowledge_base_path.exists():
        return results

    for path in sorted(knowledge_base_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.name.upper() == "README.MD":
            continue
        is_demo = DEMO_DIR_NAME in path.parts
        category = DEMO_CATEGORY_MAP.get(path.name, "other")
        try:
            added = ingest_document(path, is_demo=is_demo, category=category)
            results["documents"] += 1
            results["chunks"] += added
        except IngestionError as exc:
            results["errors"].append(str(exc))
            logger.warning("ingestion skipped file=%s error=%s", path, exc)
    return results


def seed_demo_knowledge_base_if_empty(knowledge_base_path: Path) -> dict | None:
    collection = get_collection()
    if collection.count() > 0:
        return None
    demo_dir = knowledge_base_path / DEMO_DIR_NAME
    if not demo_dir.exists():
        return None
    return reindex_all(knowledge_base_path)
