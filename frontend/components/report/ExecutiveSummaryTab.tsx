import type { FinalReport } from "@/types/api";
import { Badge } from "@/components/ui/Badge";

export function ExecutiveSummaryTab({ report }: { report: FinalReport }) {
  const passed = report.review.verdict === "PASS";
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={passed ? "brand" : "neutral"}>
          Independent review: {report.review.verdict}
        </Badge>
        {report.revision_log.length > 0 && (
          <span className="text-xs text-ink-500">
            {report.revision_log.length} revision cycle{report.revision_log.length > 1 ? "s" : ""} run
          </span>
        )}
        <span className="text-xs text-ink-400">
          Generated {new Date(report.generated_at).toLocaleString()}
        </span>
      </div>

      <div className="whitespace-pre-wrap text-sm leading-relaxed text-ink-800">{report.executive_summary}</div>

      {report.revision_log.length > 0 && (
        <div className="rounded-lg border border-ink-200 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-600">Revision Log</h3>
          <ul className="mt-2 space-y-1 text-sm text-ink-700">
            {report.revision_log.map((entry) => (
              <li key={entry.cycle}>
                Cycle {entry.cycle}: {entry.issues_raised} issue(s) raised, revised{" "}
                {entry.agents_revised.length > 0 ? entry.agents_revised.join(", ") : "no agents"} → result:{" "}
                {entry.verdict}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.review.issues.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-amber-800">
            Outstanding Reviewer Concerns
          </h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">
            {report.review.issues.map((issue, i) => (
              <li key={i}>
                <span className="font-medium">[{issue.target_agent}]</span> {issue.issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-ink-200 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-600">Key Assumptions</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-700">
            {report.key_assumptions.length === 0 && <li className="list-none text-ink-400">None identified.</li>}
            {report.key_assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-ink-200 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-600">Evidence Gaps</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-700">
            {report.evidence_gaps.length === 0 && <li className="list-none text-ink-400">None identified.</li>}
            {report.evidence_gaps.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
