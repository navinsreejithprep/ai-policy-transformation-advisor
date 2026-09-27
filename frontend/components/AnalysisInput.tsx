"use client";

import { useRef, useState } from "react";
import { DEMO_POLICY_TEXT } from "@/lib/demoPolicy";

interface Props {
  text: string;
  onTextChange: (text: string) => void;
  onStart: (policyText: string) => void;
  onUploadPdf: (file: File) => Promise<void>;
  disabled: boolean;
}

export function AnalysisInput({ text, onTextChange, onStart, onUploadPdf, disabled }: Props) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileSelected(file: File) {
    setUploading(true);
    setUploadError(null);
    try {
      await onUploadPdf(file);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const busy = disabled || uploading;

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-600">Policy / Programme</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onTextChange(DEMO_POLICY_TEXT)}
            disabled={busy}
            className="text-xs font-medium text-brand-600 hover:text-brand-700 disabled:opacity-50"
          >
            Load demo policy
          </button>
          <label className="cursor-pointer rounded-md border border-ink-200 px-3 py-1.5 text-xs font-medium text-ink-700 hover:bg-ink-50">
            {uploading ? "Uploading..." : "Upload PDF"}
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={busy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileSelected(file);
              }}
            />
          </label>
        </div>
      </div>

      {uploadError && <p className="mt-2 text-xs text-red-600">{uploadError}</p>}

      <textarea
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
        disabled={busy}
        placeholder="Paste policy/programme text (min. 20 characters), upload a PDF above, or click 'Use for analysis' on a document already in the Knowledge Base..."
        className="mt-3 h-40 w-full resize-y rounded-lg border border-ink-200 p-3 text-sm text-ink-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-ink-50"
      />
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-ink-400">{text.length} characters</span>
        <button
          onClick={() => onStart(text)}
          disabled={busy || text.trim().length < 20}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-40"
        >
          Run Advisory Analysis
        </button>
      </div>
    </section>
  );
}
