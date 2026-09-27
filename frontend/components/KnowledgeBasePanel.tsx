"use client";

import { useRef, useState } from "react";
import type { DocumentCategory, DocumentListResponse } from "@/types/api";
import { deleteDocument, getDocumentText, reindexDocuments, uploadDocument } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { RefreshIcon, SparkleIcon, TrashIcon, UploadIcon } from "@/components/ui/icons";
import { DOCUMENT_CATEGORIES } from "@/lib/categories";

interface Props {
  data: DocumentListResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onUseAsPolicyText: (text: string) => void;
}

const ALL_TAB = "all" as const;
type TabValue = DocumentCategory | typeof ALL_TAB;

function IconButton({
  title,
  onClick,
  disabled,
  tone = "neutral",
  children,
}: {
  title: string;
  onClick: () => void;
  disabled?: boolean;
  tone?: "neutral" | "danger";
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      aria-label={title}
      className={`rounded-md p-1.5 disabled:opacity-40 ${
        tone === "danger" ? "text-ink-400 hover:bg-red-50 hover:text-red-600" : "text-ink-400 hover:bg-ink-100 hover:text-ink-700"
      }`}
    >
      {children}
    </button>
  );
}

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

  const activeCategory = activeTab === ALL_TAB ? null : DOCUMENT_CATEGORIES.find((c) => c.value === activeTab);
  const visibleDocuments = data?.documents.filter((d) => activeTab === ALL_TAB || d.category === activeTab) ?? [];

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-600">Knowledge Base</h2>
        <div className="flex items-center gap-0.5">
          <IconButton title="Re-index all" onClick={handleReindex} disabled={busy}>
            <RefreshIcon />
          </IconButton>
          <label
            title="Upload PDF"
            className={`cursor-pointer rounded-md p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-700 ${busy ? "pointer-events-none opacity-40" : ""}`}
          >
            <UploadIcon />
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={busy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUpload(file, activeTab === ALL_TAB ? undefined : activeTab);
              }}
            />
          </label>
        </div>
      </div>

      {loading && <p className="mt-3 text-sm text-ink-400">Loading...</p>}
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {data && (
        <>
          <p className="mt-1 text-xs text-ink-400">
            {data.documents.length} documents · {data.total_chunks} chunks
            {data.last_indexed_at && ` · indexed ${new Date(data.last_indexed_at).toLocaleString()}`}
          </p>

          <select
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value as TabValue)}
            className="mt-3 w-full rounded-md border border-ink-200 bg-white px-2 py-1.5 text-sm text-ink-800 focus:border-brand-500 focus:outline-none"
          >
            <option value={ALL_TAB}>All categories ({data.documents.length})</option>
            {DOCUMENT_CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label} ({data.documents.filter((d) => d.category === cat.value).length})
              </option>
            ))}
          </select>
          {activeCategory && <p className="mt-1 text-xs text-ink-400">{activeCategory.hint}</p>}

          {actionError && <p className="mt-2 text-sm text-red-600">{actionError}</p>}

          <ul className="mt-2 max-h-80 divide-y divide-ink-100 overflow-y-auto">
            {visibleDocuments.map((doc) => (
              <li key={doc.document_name} className="flex items-center justify-between gap-2 py-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="truncate text-sm text-ink-800">{doc.document_name}</span>
                    {doc.is_demo_data && <Badge tone="demo">DEMO</Badge>}
                  </div>
                  <div className="text-xs text-ink-400">{doc.chunks} chunks · {doc.pages} pages</div>
                </div>
                <div className="flex flex-shrink-0 items-center gap-0.5">
                  <IconButton title="Use for analysis" onClick={() => handleUseForAnalysis(doc.document_name)} disabled={busy}>
                    <SparkleIcon />
                  </IconButton>
                  <IconButton title="Delete" tone="danger" onClick={() => handleDelete(doc.document_name)} disabled={busy}>
                    <TrashIcon />
                  </IconButton>
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
