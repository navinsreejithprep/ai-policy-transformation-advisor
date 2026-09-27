import type { BenchmarkReport } from "@/types/api";
import { Badge } from "@/components/ui/Badge";

export function BenchmarkTab({ report }: { report: BenchmarkReport }) {
  if (report.benchmarks.length === 0) {
    return <p className="text-sm text-ink-400">No comparable programmes found in the knowledge base.</p>;
  }

  return (
    <div className="space-y-4">
      {report.benchmarks.map((b, i) => (
        <div key={i} className="rounded-lg border border-ink-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold text-ink-900">{b.name}</h3>
            <Badge tone={b.comparability_supported_by_evidence ? "brand" : "neutral"}>
              {b.comparability_supported_by_evidence ? "Comparability evidenced" : "Comparability not established"}
            </Badge>
          </div>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium uppercase text-ink-500">Objective</dt>
              <dd className="text-sm text-ink-700">{b.objective}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase text-ink-500">Approach</dt>
              <dd className="text-sm text-ink-700">{b.approach}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase text-ink-500">Implementation Model</dt>
              <dd className="text-sm text-ink-700">{b.implementation_model}</dd>
            </div>
            {b.funding && (
              <div>
                <dt className="text-xs font-medium uppercase text-ink-500">Funding</dt>
                <dd className="text-sm text-ink-700">{b.funding}</dd>
              </div>
            )}
            {b.governance && (
              <div>
                <dt className="text-xs font-medium uppercase text-ink-500">Governance</dt>
                <dd className="text-sm text-ink-700">{b.governance}</dd>
              </div>
            )}
            {b.outcomes && (
              <div>
                <dt className="text-xs font-medium uppercase text-ink-500">Outcomes</dt>
                <dd className="text-sm text-ink-700">{b.outcomes}</dd>
              </div>
            )}
          </dl>
          {b.lessons.length > 0 && (
            <div className="mt-3">
              <dt className="text-xs font-medium uppercase text-ink-500">Lessons</dt>
              <ul className="mt-1 list-disc pl-5 text-sm text-ink-700">
                {b.lessons.map((l, j) => (
                  <li key={j}>{l}</li>
                ))}
              </ul>
            </div>
          )}
          {b.sources.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-500">
              {b.sources.map((s, j) => (
                <span key={j}>
                  {s.document_name}
                  {s.page_number ? `, p. ${s.page_number}` : ""}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
