import type { EvidenceReport } from "@/types/api";
import { LevelBadge, Badge } from "@/components/ui/Badge";
import { confidenceBarWidth } from "@/lib/levels";

export function EvidenceTab({ evidence }: { evidence: EvidenceReport }) {
  return (
    <div className="space-y-6">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-ink-200 text-left text-xs uppercase tracking-wide text-ink-500">
              <th className="py-2 pr-3">Claim</th>
              <th className="py-2 pr-3">Evidence</th>
              <th className="py-2 pr-3">Source</th>
              <th className="py-2 pr-3">Confidence</th>
              <th className="py-2 pr-3">Contradiction</th>
            </tr>
          </thead>
          <tbody>
            {evidence.findings.map((f, i) => (
              <tr key={i} className="border-b border-ink-100 align-top">
                <td className="py-3 pr-3 font-medium text-ink-900">{f.claim}</td>
                <td className="py-3 pr-3 text-ink-700">{f.evidence}</td>
                <td className="py-3 pr-3">
                  <div className="flex flex-col gap-1">
                    {f.sources.length === 0 && <span className="text-xs text-ink-400">No source</span>}
                    {f.sources.map((s, j) => (
                      <span key={j} className="flex items-center gap-1 text-xs text-ink-600">
                        {s.document_name}
                        {s.page_number ? `, p. ${s.page_number}` : ""}
                        {s.is_demo_data && <Badge tone="demo">DEMO</Badge>}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-3 pr-3">
                  <div className="flex items-center gap-2">
                    <LevelBadge level={f.confidence} />
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-ink-100">
                      <div className={`h-full rounded-full bg-brand-500 ${confidenceBarWidth(f.confidence)}`} />
                    </div>
                  </div>
                </td>
                <td className="py-3 pr-3 text-ink-600">{f.contradiction ?? "—"}</td>
              </tr>
            ))}
            {evidence.findings.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-ink-400">
                  No evidence findings.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="rounded-lg border border-ink-200 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-600">Evidence Gaps</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-700">
          {evidence.evidence_gaps.length === 0 && (
            <li className="list-none text-ink-400">Insufficient evidence in the available knowledge base. None flagged.</li>
          )}
          {evidence.evidence_gaps.map((g, i) => (
            <li key={i}>{g}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
