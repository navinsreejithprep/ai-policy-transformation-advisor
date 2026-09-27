import fitz
from fastapi.testclient import TestClient

from app.main import app


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()


def test_health(isolated_kb):
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_documents_empty_on_fresh_kb(isolated_kb):
    with TestClient(app) as client:
        resp = client.get("/documents")
        assert resp.status_code == 200
        body = resp.json()
        assert body["documents"] == []
        assert body["total_chunks"] == 0


def test_upload_rejects_non_pdf(isolated_kb):
    with TestClient(app) as client:
        resp = client.post(
            "/documents/upload", files={"file": ("notes.txt", b"hello world", "text/plain")}
        )
        assert resp.status_code == 400


def test_upload_rejects_empty_file(isolated_kb):
    with TestClient(app) as client:
        resp = client.post("/documents/upload", files={"file": ("empty.pdf", b"", "application/pdf")})
        assert resp.status_code == 400


def test_upload_then_list_then_delete(isolated_kb):
    pdf_bytes = _make_pdf_bytes("Digital Service Access Improvement Programme test content.")
    with TestClient(app) as client:
        upload_resp = client.post(
            "/documents/upload", files={"file": ("test_policy.pdf", pdf_bytes, "application/pdf")}
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["chunks_added"] > 0

        list_resp = client.get("/documents")
        assert list_resp.status_code == 200
        docs = list_resp.json()["documents"]
        # No category was specified — must default quietly to "other", never be required.
        assert any(
            d["document_name"] == "test_policy.pdf" and d["is_demo_data"] is False and d["category"] == "other"
            for d in docs
        )

        delete_resp = client.delete("/documents/test_policy.pdf")
        assert delete_resp.status_code == 200

        list_resp_after = client.get("/documents")
        assert list_resp_after.json()["total_chunks"] == 0


def test_upload_with_explicit_category(isolated_kb):
    pdf_bytes = _make_pdf_bytes("A prior rollout risk case study.")
    with TestClient(app) as client:
        upload_resp = client.post(
            "/documents/upload",
            files={"file": ("risk_note.pdf", pdf_bytes, "application/pdf")},
            data={"category": "risk"},
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["category"] == "risk"

        docs = client.get("/documents").json()["documents"]
        assert any(d["document_name"] == "risk_note.pdf" and d["category"] == "risk" for d in docs)


def test_upload_rejects_invalid_category(isolated_kb):
    pdf_bytes = _make_pdf_bytes("content")
    with TestClient(app) as client:
        resp = client.post(
            "/documents/upload",
            files={"file": ("x.pdf", pdf_bytes, "application/pdf")},
            data={"category": "not-a-real-category"},
        )
        assert resp.status_code == 422


def test_delete_unknown_document_returns_404(isolated_kb):
    with TestClient(app) as client:
        resp = client.delete("/documents/does_not_exist.pdf")
        assert resp.status_code == 404


def test_get_document_text_returns_extracted_content(isolated_kb):
    pdf_bytes = _make_pdf_bytes("Digital Service Access Improvement Programme test content.")
    with TestClient(app) as client:
        client.post("/documents/upload", files={"file": ("policy_for_analysis.pdf", pdf_bytes, "application/pdf")})

        resp = client.get("/documents/policy_for_analysis.pdf/text")
        assert resp.status_code == 200
        body = resp.json()
        assert body["document_name"] == "policy_for_analysis.pdf"
        assert "Digital Service Access Improvement Programme" in body["text"]


def test_get_document_text_unknown_document_returns_404(isolated_kb):
    with TestClient(app) as client:
        resp = client.get("/documents/does_not_exist.pdf/text")
        assert resp.status_code == 404
