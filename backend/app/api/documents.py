from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..config import settings
from ..models.schemas import DocumentCategory, DocumentInfo, DocumentListResponse
from ..rag.ingest import IngestionError, delete_document, ingest_pdf, reindex_all
from ..rag.retrieve import get_document_text
from ..rag.store import get_collection
from ..services import kb_meta
from ..utils.logging import get_logger

router = APIRouter(tags=["documents"])
logger = get_logger(__name__)

def _upload_dir() -> Path:
    return Path(settings.knowledge_base_path) / "uploads"


@router.get("/documents", response_model=DocumentListResponse)
def list_documents():
    collection = get_collection()
    data = collection.get(include=["metadatas"])
    metadatas = data.get("metadatas", []) or []

    by_document: dict[str, dict] = {}
    for m in metadatas:
        if not m:
            continue
        name = m.get("document_name")
        entry = by_document.setdefault(name, {"chunks": 0, "pages": set(), "is_demo": False, "category": "other"})
        entry["chunks"] += 1
        entry["pages"].add(m.get("page_number"))
        entry["is_demo"] = entry["is_demo"] or bool(m.get("is_demo_data"))
        entry["category"] = m.get("category") or entry["category"]

    documents = [
        DocumentInfo(
            document_name=name,
            chunks=info["chunks"],
            pages=len(info["pages"]),
            is_demo_data=info["is_demo"],
            category=info["category"],
        )
        for name, info in sorted(by_document.items())
    ]
    return DocumentListResponse(
        documents=documents,
        total_chunks=collection.count(),
        last_indexed_at=kb_meta.get_last_indexed_at(),
    )


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: DocumentCategory = Form(default=DocumentCategory.OTHER),
):
    """`category` is optional, informational-only tagging (spec: never mandatory) —
    it helps the Knowledge Base UI show what a document is for, but an uploaded
    document with no category (or the default "other") ingests and retrieves
    exactly the same as any other document."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported for upload.")

    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"File exceeds the {settings.max_upload_mb}MB upload limit.")
    if len(content) == 0:
        raise HTTPException(400, "Uploaded file is empty.")

    upload_dir = _upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / Path(file.filename).name
    destination.write_bytes(content)

    try:
        count = ingest_pdf(destination, is_demo=False, category=category.value)
    except IngestionError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc

    kb_meta.mark_indexed()
    logger.info("uploaded document=%s chunks=%d category=%s", file.filename, count, category.value)
    return {"document": file.filename, "chunks_added": count, "category": category.value}


@router.get("/documents/{document_name}/text")
def get_document_full_text(document_name: str):
    """Reconstructs a document's full text from its indexed chunks — used by the
    frontend's "Use as policy input" action so an uploaded PDF can be analyzed
    directly instead of requiring the user to copy-paste its content."""
    text = get_document_text(document_name)
    if not text:
        raise HTTPException(404, f"No content found for document '{document_name}'.")
    return {"document_name": document_name, "text": text}


@router.post("/documents/index")
def reindex():
    """Rebuild the entire vector store from every file currently on disk under
    knowledge_base/ (demo + uploads). Useful after manually dropping files in."""
    results = reindex_all(Path(settings.knowledge_base_path))
    kb_meta.mark_indexed()
    logger.info("reindexed documents=%d chunks=%d errors=%d", results["documents"], results["chunks"], len(results["errors"]))
    return results


@router.delete("/documents/{document_name}")
def remove_document(document_name: str):
    removed = delete_document(document_name)
    if removed == 0:
        raise HTTPException(404, f"No chunks found for document '{document_name}'.")

    # Also remove the underlying file (wherever it lives under knowledge_base/) so a
    # later POST /documents/index doesn't silently resurrect it from disk.
    for match in Path(settings.knowledge_base_path).rglob(document_name):
        if match.is_file():
            match.unlink()

    kb_meta.mark_indexed()
    return {"document": document_name, "chunks_removed": removed}
