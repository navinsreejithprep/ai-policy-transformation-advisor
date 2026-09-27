"use client";

import { useRef, useState } from "react";
import type { DocumentCategory, DocumentListResponse } from "@/types/api";
import { deleteDocument, getDocumentText, reindexDocuments, uploadDocument } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { DOCUMENT_CATEGORIES, categoryLabel } from "@/lib/categories";

interface Props {
  data: DocumentListResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onUseAsPolicyText: (text: string) => void;
}

const ALL_TAB = "all" as const;
type TabValue = DocumentCategory | typeof ALL_TAB;

export function KnowledgeBasePanel({ data, loading, error, onRefresh, onUseAsPolicyText }: Props) {
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabValue>(ALL_TAB);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleUpload(file: File, category?: DocumentCategory) {
    setBusy(true);
    setActionError(null);
    try {
      await uploadDocument(file, category);
      onRefresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(name: string) {
    setBusy(true);
    setActionError(null);
    try {
      await deleteDocument(name);
      onRefresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Delete failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReindex() {
    setBusy(true);
    setActionError(null);
    try {
      await reindexDocuments();
      onRefresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Reindex failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUseForAnalysis(name: string) {
    setBusy(true);
    setActionError(null);
    try {
      const { text } = await getDocumentText(name);
      onUseAsPolicyText(text);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not load document text.");
    } finally {
      setBusy(false);
    }
  }

  const activeHint =
    activeTab === ALL_TAB
      ? "All documents currently in the knowledge base."
      : DOCUMENT_CATEGORIES.find((c) => c.value === activeTab)?.hint;

  const visibleDocuments = data?.documents.filter((d) => activeTab === ALL_TAB || d.category === activeTab) ?? [];

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-600">Knowledge Base</h2>
        <button
          onClick={handleReindex}
          disabled={busy}
          className="rounded-md border border-ink-200 px-3 py-1.5 text-xs font-medium text-ink-700 hover:bg-ink-50 disabled:opacity-50"
        >
          Re-index all
        </button>
      </div>
      <p className="mt-1 text-xs text-ink-400">
        Not sure what to add? The tabs below are just suggestions of what's useful — nothing here is required.
      </p>

      {loading && <p className="mt-3 text-sm text-ink-400">Loading...</p>}
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {data && (
        <>
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <div className="rounded-lg bg-ink-50 py-3">
              <div className="text-2xl font-semibold text-ink-900">{data.documents.length}</div>
              <div className="text-xs text-ink-500">documents</div>
            </div>
            <div className="rounded-lg bg-ink-50 py-3">
              <div className="text-2xl font-semibold text-ink-900">{data.total_chunks}</div>
              <div className="text-xs text-ink-500">chunks indexed</div>
            </div>
            <div className="rounded-lg bg-ink-50 py-3">
              <div className="text-sm font-medium text-ink-900">
                {data.last_indexed_at ? new Date(data.last_indexed_at).toLocaleString() : "—"}
              </div>
              <div className="text-xs text-ink-500">last indexed</div>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-1 border-b border-ink-200 pb-2">
            <button
              onClick={() => setActiveTab(ALL_TAB)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium ${
                activeTab === ALL_TAB ? "bg-brand-100 text-brand-700" : "text-ink-500 hover:bg-ink-50"
              }`}
            >
              All ({data.documents.length})
            </button>
            {DOCUMENT_CATEGORIES.map((cat) => {
              const count = data.documents.filter((d) => d.category === cat.value).length;
              return (
                <button
                  key={cat.value}
                  onClick={() => setActiveTab(cat.value)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium ${
                    activeTab === cat.value ? "bg-brand-100 text-brand-700" : "text-ink-500 hover:bg-ink-50"
                  }`}
                >
                  {cat.label} ({count})
                </button>
              );
            })}
          </div>

          <div className="mt-3 flex items-start justify-between gap-3 rounded-lg bg-ink-50 p-3">
            <p className="text-xs text-ink-600">{activeHint}</p>
            {activeTab !== ALL_TAB && (
              <label className="flex-shrink-0 cursor-pointer rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700">
                Upload PDF
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  disabled={busy}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleUpload(file, activeTab);
                  }}
                />
              </label>
            )}
          </div>

          {actionError && <p className="mt-2 text-sm text-red-600">{actionError}</p>}

          <ul className="mt-2 divide-y divide-ink-100">
            {visibleDocuments.map((doc) => (
              <li key={doc.document_name} className="flex items-center justify-between py-2 text-sm">
                <div className="flex min-w-0 items-center gap-2">
                  <span className="truncate text-ink-800">{doc.document_name}</span>
                  {doc.is_demo_data && <Badge tone="demo">DEMO</Badge>}
                  {activeTab === ALL_TAB && <Badge tone="neutral">{categoryLabel(doc.category)}</Badge>}
                  <span className="flex-shrink-0 text-xs text-ink-400">
                    {doc.chunks} chunks · {doc.pages} pages
                  </span>
                </div>
                <div className="flex flex-shrink-0 items-center gap-3">
                  <button
                    onClick={() => handleUseForAnalysis(doc.document_name)}
                    disabled={busy}
                    className="text-xs font-medium text-brand-600 hover:text-brand-800 disabled:opacity-50"
                  >
                    Use for analysis
                  </button>
                  <button
                    onClick={() => handleDelete(doc.document_name)}
                    disabled={busy}
                    className="text-xs font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
            {visibleDocuments.length === 0 && (
              <li className="py-3 text-sm text-ink-400">No documents here yet — uploading is optional.</li>
            )}
          </ul>
        </>
      )}
    </section>
  );
}
