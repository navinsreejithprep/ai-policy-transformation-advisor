import type { AnalysisJobStatus, AnalysisStage } from "@/types/api";

const STEPS: { stage: AnalysisStage; label: string }[] = [
  { stage: "policy_analysis", label: "Policy Analysis" },
  { stage: "evidence_research", label: "Evidence Research" },
  { stage: "stakeholder_analysis", label: "Stakeholder Analysis" },
  { stage: "risk_assessment", label: "Risk Assessment" },
  { stage: "benchmarking", label: "Benchmarking" },
  { stage: "implementation_planning", label: "Implementation Planning" },
  { stage: "independent_review", label: "Independent Review" },
  { stage: "synthesis", label: "Synthesis" },
];

function stepStatus(step: AnalysisStage, current: AnalysisStage): "done" | "active" | "pending" {
  const order = STEPS.map((s) => s.stage);
  const currentIndex = current === "revision" ? order.indexOf("independent_review") : order.indexOf(current);
  const stepIndex = order.indexOf(step);
  if (current === "complete") return "done";
  if (stepIndex < currentIndex) return "done";
  if (stepIndex === currentIndex) return "active";
  return "pending";
}

export function AnalysisProgress({ status }: { status: AnalysisJobStatus }) {
  if (status.stage === "failed") {
    return (
      <section className="card border-red-200 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-red-600">Analysis Failed</h2>
        <p className="mt-2 text-sm text-red-700">{status.error}</p>
      </section>
    );
  }

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-600">Analysis in Progress</h2>
        <span className="text-xs text-ink-400">{status.progress_pct}%</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
        <div
          className="h-full rounded-full bg-brand-600 transition-all duration-500"
          style={{ width: `${status.progress_pct}%` }}
        />
      </div>
      {status.stage === "revision" && (
        <p className="mt-2 text-xs font-medium text-amber-700">
          Independent reviewer requested revisions — re-running flagged agents...
        </p>
      )}
      <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {STEPS.map((step) => {
          const s = stepStatus(step.stage, status.stage);
          return (
            <li
              key={step.stage}
              className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-xs ${
                s === "active"
                  ? "bg-brand-100 font-medium text-brand-700"
                  : s === "done"
                  ? "text-emerald-700"
                  : "text-ink-400"
              }`}
            >
              <span
                className={`h-2 w-2 flex-shrink-0 rounded-full ${
                  s === "active" ? "animate-pulse bg-brand-600" : s === "done" ? "bg-emerald-500" : "bg-ink-300"
                }`}
              />
              {step.label}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
