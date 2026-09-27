"use client";

import { useState } from "react";
import type { SourceCitation } from "@/types/api";
import { Badge } from "@/components/ui/Badge";

export function SourcesTab({ sources }: { sources: SourceCitation[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (sources.length === 0) {
    return <p className="text-sm text-ink-400">No sources were cited for this analysis.</p>;
  }

  return (
    <ul className="space-y-2">
      {sources.map((s, i) => (
        <li key={i} className="rounded-lg border border-ink-200">
          <button
            onClick={() => setExpanded(expanded === i ? null : i)}
            disabled={!s.passage_preview}
            className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left disabled:cursor-default"
          >
            <span className="text-sm text-ink-800">
              [{i + 1}] {s.document_name}
              {s.page_number ? `, p. ${s.page_number}` : ""}
              {s.section ? ` — ${s.section}` : ""}
            </span>
            <span className="flex items-center gap-2">
              {s.is_demo_data && <Badge tone="demo">DEMO</Badge>}
              {s.passage_preview && (
                <span className="text-xs text-brand-600">{expanded === i ? "Hide passage" : "View passage"}</span>
              )}
            </span>
          </button>
          {expanded === i && s.passage_preview && (
            <div className="border-t border-ink-100 bg-ink-50 px-4 py-3 text-sm italic text-ink-700">
              "{s.passage_preview}"
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
