# RAG Design

## Pipeline

```text
PDF / TXT / MD
    |
    v
Text extraction (PyMuPDF per-page for PDF; whole-file for TXT/MD, with optional
    |            `[PAGE n]` markers for realistic multi-page citations — see below)
    v
Cleaning (strip control chars, collapse whitespace — app/rag/ingest.py::clean_text)
    |
    v
Chunking (900 chars, 120 overlap, configurable via CHUNK_SIZE/CHUNK_OVERLAP)
    |
    v
Embedding (sentence-transformers/all-MiniLM-L6-v2, configurable)
    |
    v
ChromaDB (persistent, cosine space) — one collection, metadata-filterable
    |
    v
retrieve_evidence(): over-fetch -> relevance threshold -> dedup -> top_k
    |
    v
Agent context (formatted as "[document_name, page N] passage text")
```

## Chunk metadata

Every chunk stores: `document_name`, `document_type` (`pdf`/`text`), `page_number`, `section`
(best-effort heuristic — see below), `source` (file path), `publication_date` (currently always empty —
no PDF/text metadata extraction implemented for this field, left as a documented gap), `chunk_id`
(unique, used for dedup and the "view passage" UI feature), `is_demo_data` (bool, drives the DEMO badge
in the UI).

**Section detection is a heuristic, not real document structure parsing**: for each page (PDF) or
page-like block (`.txt`/`.md`), the *first line of that page's raw text* — before chunking collapses line
breaks — is treated as a section heading if it's short (3-80 chars) and doesn't end in a period
(`app/rag/ingest.py::_detect_section_heading`), and every chunk from that page inherits the same section
label. This is explicitly a design choice for a POC, not a real outline/heading parser — flagged here so
it isn't mistaken for something more robust than it is.

**Multi-page plain-text demo docs**: PyMuPDF gives real page numbers for PDFs for free. Plain-text/
Markdown files don't have "pages," but citations look more credible when they do (the spec's own example
is `[Source: Annual Report 2025, p. 43]`), so `.txt`/`.md` files can opt into page-like citations by
inserting a `[PAGE 43]` marker line — see `backend/knowledge_base/demo/annual_report_2025_excerpt.txt`
for a worked example. Files with no markers are treated as a single page.

## Retrieval

`retrieve_evidence(query, top_k, filters, relevance_threshold)` in `app/rag/retrieve.py`:

- **Semantic search**: cosine similarity via ChromaDB
- **Over-fetch**: requests `max(top_k*3, top_k)` candidates so thresholding/dedup still leaves ~`top_k`
  useful results
- **Relevance threshold**: `RETRIEVAL_RELEVANCE_THRESHOLD` (default 0.35) — hits below this similarity
  are dropped rather than forced into the context, so an out-of-scope query correctly returns nothing
  (verified by the "negative control" case in the evaluation set)
- **Metadata filtering**: `filters` is passed straight through to ChromaDB's `where=`, e.g. to restrict
  to a single document
- **Source dedup**: at most one chunk per (document, page) pair, keeping the highest-similarity one
- **Similarity score is kept internally for ranking/thresholding but not surfaced to end users** — the
  API and UI show the document/page citation, not a raw cosine number, per the spec's guidance that raw
  scores aren't meaningful to a non-technical reader

## Known limitations (explicit, not hidden)

- No hybrid BM25 + vector retrieval — pure dense search only
- No reranking model
- No document-level access control (anyone hitting the API can retrieve from the whole KB)
- `publication_date` metadata is never populated — no extraction logic exists for it yet
- Section detection is a heuristic (see above), not real structural parsing
- Retrieval evaluation (`app/evaluation/run.py`) covers exactly one small synthetic corpus and 15
  hand-written questions — see `docs/evaluation.md` for what that does and doesn't tell you
